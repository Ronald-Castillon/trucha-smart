"""Motor y sesiones de SQLAlchemy (PostgreSQL o SQLite, ADR-003)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Engine, create_engine, event, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class FechaHoraUTC(TypeDecorator):
    """Guarda fechas en UTC y las devuelve siempre con zona horaria (SQLite no la conserva)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, valor: datetime | None, dialect):
        if valor is None:
            return None
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=UTC)
        valor = valor.astimezone(UTC)
        return valor.replace(tzinfo=None) if dialect.name == "sqlite" else valor

    def process_result_value(self, valor: datetime | None, dialect):
        if valor is None:
            return None
        return valor.replace(tzinfo=UTC) if valor.tzinfo is None else valor.astimezone(UTC)


def crear_motor(url: str) -> Engine:
    if url.startswith("sqlite"):
        opciones: dict = {"connect_args": {"check_same_thread": False, "timeout": 15}}
        en_memoria = url in ("sqlite://", "sqlite:///:memory:")
        if en_memoria:
            opciones["poolclass"] = StaticPool
        else:
            # Defecto #39: el pool por defecto (5 + 10) se agotaba con los 40 hilos de cada worker.
            opciones.update(pool_size=20, max_overflow=30)
        motor = create_engine(url, **opciones)

        @event.listens_for(motor, "connect")
        def _configurar(conexion, _):
            conexion.execute("PRAGMA foreign_keys = ON")
            if not en_memoria:
                # Defecto #39: con el diario por defecto, una escritura bloquea a los lectores y
                # bajo carga aparecían 500 "database is locked". WAL permite leer mientras se
                # escribe; busy_timeout espera el turno en lugar de fallar.
                # busy_timeout primero: varios workers arrancan a la vez y cambian el modo.
                conexion.execute("PRAGMA busy_timeout = 15000")
                conexion.execute("PRAGMA journal_mode = WAL")

        return motor
    # pool_pre_ping descarta conexiones rotas: tras una caída de PostgreSQL reconecta (RNF-R)
    # 4 workers x (10 + 15) = 100 conexiones como máximo, el límite por defecto de PostgreSQL.
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=15,
        connect_args={"connect_timeout": 3},
    )


class BaseDatos:
    def __init__(self, url: str) -> None:
        self.motor = crear_motor(url)
        self.fabrica = sessionmaker(bind=self.motor, expire_on_commit=False)

    def crear_tablas(self) -> None:
        from src.adapters.outbound.persistence import orm  # noqa: F401  registra modelos

        Base.metadata.create_all(self.motor)
        self._migrar_columnas()

    def _migrar_columnas(self) -> None:
        """Agrega columnas nuevas a tablas creadas por versiones anteriores (Inc3, RF-11)."""
        nuevas = {
            "usuarios": {
                "intentos_fallidos": "INTEGER NOT NULL DEFAULT 0",
                "bloqueado_hasta": "TIMESTAMP WITH TIME ZONE",
            }
        }
        inspector = inspect(self.motor)
        with self.motor.begin() as conexion:
            for tabla, columnas in nuevas.items():
                existentes = {c["name"] for c in inspector.get_columns(tabla)}
                for nombre, tipo in columnas.items():
                    if nombre not in existentes:
                        conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}"))

    def disponible(self) -> bool:
        """Comprueba la conexión con `SELECT 1` (usado por /api/salud, RNF-R)."""
        try:
            with self.motor.connect() as conexion:
                conexion.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def sesion(self) -> Session:
        return self.fabrica()
