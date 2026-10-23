"""Modelos ORM (SQLAlchemy 2). Reflejan db/schema.sql; el dominio no los conoce."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.outbound.persistence.db import Base, FechaHoraUTC


class UsuarioORM(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("rol IN ('ADMINISTRADOR', 'PISCICULTOR', 'OPERARIO')", name="ck_rol"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_usuario: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(FechaHoraUTC, nullable=False)


def _decimal(precision: int = 10, escala: int = 2) -> Numeric:
    return Numeric(precision, escala, asdecimal=False)


class EstanqueORM(Base):
    __tablename__ = "estanques"
    __table_args__ = (CheckConstraint("tipo IN ('ESTANQUE', 'JAULA')", name="ck_tipo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    volumen_m3: Mapped[float | None] = mapped_column(_decimal())
    ubicacion: Mapped[str | None] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(FechaHoraUTC, nullable=False)


class LoteORM(Base):
    __tablename__ = "lotes"
    __table_args__ = (
        CheckConstraint("num_peces_inicial > 0", name="ck_peces"),
        CheckConstraint("peso_medio_inicial_g > 0", name="ck_peso_inicial"),
        CheckConstraint("peso_medio_actual_g > 0", name="ck_peso_actual"),
        Index("ix_lotes_estanque", "estanque_id"),
        Index(
            "ux_lotes_un_activo_por_estanque",
            "estanque_id",
            unique=True,
            sqlite_where=text("activo"),
            postgresql_where=text("activo"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estanque_id: Mapped[int] = mapped_column(ForeignKey("estanques.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    num_peces_inicial: Mapped[int] = mapped_column(Integer, nullable=False)
    peso_medio_inicial_g: Mapped[float] = mapped_column(_decimal(), nullable=False)
    peso_medio_actual_g: Mapped[float] = mapped_column(_decimal(), nullable=False)
    fecha_siembra: Mapped[date] = mapped_column(Date, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_cierre: Mapped[date | None] = mapped_column(Date)


class LecturaAguaORM(Base):
    __tablename__ = "lecturas_agua"
    __table_args__ = (
        CheckConstraint("temperatura_c BETWEEN 0 AND 40", name="ck_temperatura"),
        CheckConstraint("oxigeno_mg_l >= 0", name="ck_oxigeno"),
        CheckConstraint("ph BETWEEN 0 AND 14", name="ck_ph"),
        CheckConstraint("fuente IN ('MANUAL', 'SENSOR')", name="ck_fuente"),
        Index("ix_lecturas_estanque_fecha", "estanque_id", "medido_en"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estanque_id: Mapped[int] = mapped_column(ForeignKey("estanques.id"), nullable=False)
    temperatura_c: Mapped[float] = mapped_column(_decimal(5, 2), nullable=False)
    oxigeno_mg_l: Mapped[float] = mapped_column(_decimal(5, 2), nullable=False)
    ph: Mapped[float] = mapped_column(_decimal(4, 2), nullable=False)
    fuente: Mapped[str] = mapped_column(String(10), nullable=False)
    registrado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    medido_en: Mapped[datetime] = mapped_column(FechaHoraUTC, nullable=False)


class AlertaORM(Base):
    __tablename__ = "alertas"
    __table_args__ = (
        CheckConstraint(
            "parametro IN ('TEMPERATURA', 'OXIGENO_DISUELTO', 'PH')", name="ck_parametro"
        ),
        CheckConstraint("nivel IN ('PRECAUCION', 'CRITICA')", name="ck_nivel"),
        CheckConstraint("estado IN ('ABIERTA', 'ATENDIDA')", name="ck_estado"),
        CheckConstraint(
            "estado = 'ABIERTA' OR (atendida_por IS NOT NULL AND atendida_en IS NOT NULL)",
            name="ck_atencion",
        ),
        Index("ix_alertas_estanque_fecha", "estanque_id", "creada_en"),
        Index("ix_alertas_abiertas", "estanque_id", "parametro", "nivel", "estado"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estanque_id: Mapped[int] = mapped_column(ForeignKey("estanques.id"), nullable=False)
    lectura_id: Mapped[int] = mapped_column(
        ForeignKey("lecturas_agua.id", ondelete="CASCADE"), nullable=False
    )
    parametro: Mapped[str] = mapped_column(String(20), nullable=False)
    nivel: Mapped[str] = mapped_column(String(12), nullable=False)
    valor: Mapped[float] = mapped_column(_decimal(6, 2), nullable=False)
    mensaje: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default="ABIERTA")
    creada_en: Mapped[datetime] = mapped_column(FechaHoraUTC, nullable=False)
    atendida_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    atendida_en: Mapped[datetime | None] = mapped_column(FechaHoraUTC)
    observacion: Mapped[str | None] = mapped_column(String(255))
