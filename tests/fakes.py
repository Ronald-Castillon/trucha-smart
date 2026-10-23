"""Dobles de prueba de los puertos de salida (sin BD ni frameworks)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from src.domain.model.usuario import Usuario


class RelojFijo:
    def __init__(self, momento: datetime | None = None) -> None:
        self.momento = momento or datetime(2026, 10, 23, 12, 0, tzinfo=UTC)

    def ahora(self) -> datetime:
        return self.momento

    def avanzar(self, **kwargs) -> None:
        self.momento += timedelta(**kwargs)


class HasherFalso:
    def hashear(self, password: str) -> str:
        return f"hash:{password}"

    def verificar(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hash:{password}"


class RepositorioMemoria:
    """Repositorio genérico en memoria: asigna ids incrementales y guarda copias."""

    def __init__(self) -> None:
        self.datos: dict[int, object] = {}
        self._siguiente = 1

    def guardar(self, entidad):
        if entidad.id is None:
            entidad = replace(entidad, id=self._siguiente)
            self._siguiente += 1
        self.datos[entidad.id] = replace(entidad)
        return replace(entidad)

    def por_id(self, entidad_id: int):
        e = self.datos.get(entidad_id)
        return replace(e) if e else None

    def listar(self):
        return [replace(e) for e in self.datos.values()]


class RepositorioUsuarioMemoria(RepositorioMemoria):
    def por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        return next(
            (replace(u) for u in self.datos.values() if u.nombre_usuario == nombre_usuario), None
        )


class RepositorioEstanqueMemoria(RepositorioMemoria):
    def por_nombre(self, nombre: str):
        return next((replace(e) for e in self.datos.values() if e.nombre == nombre), None)

    def listar(self, solo_activos: bool = True):
        return [replace(e) for e in self.datos.values() if e.activo or not solo_activos]


class RepositorioLoteMemoria(RepositorioMemoria):
    def por_codigo(self, codigo: str):
        return next((replace(lo) for lo in self.datos.values() if lo.codigo == codigo), None)

    def activo_de(self, estanque_id: int):
        return next(
            (
                replace(lo)
                for lo in self.datos.values()
                if lo.estanque_id == estanque_id and lo.activo
            ),
            None,
        )

    def de_estanque(self, estanque_id: int):
        return [replace(lo) for lo in self.datos.values() if lo.estanque_id == estanque_id]


class RepositorioLecturaMemoria(RepositorioMemoria):
    def ultima_de(self, estanque_id: int):
        lecturas = self.de_estanque(estanque_id)
        return lecturas[0] if lecturas else None

    def de_estanque(self, estanque_id, desde=None, hasta=None, limite=None):
        res = [
            replace(x)
            for x in self.datos.values()
            if x.estanque_id == estanque_id
            and (desde is None or x.medido_en >= desde)
            and (hasta is None or x.medido_en <= hasta)
        ]
        res.sort(key=lambda x: (x.medido_en, x.id), reverse=True)
        return res[:limite] if limite else res


class RepositorioAlertaMemoria(RepositorioMemoria):
    def abierta(self, estanque_id, parametro, nivel):
        return next(
            (
                replace(a)
                for a in self.datos.values()
                if a.estanque_id == estanque_id
                and a.parametro == parametro
                and a.nivel == nivel
                and a.abierta
            ),
            None,
        )

    def listar(self, estanque_id=None, estado=None, limite=None):
        res = [
            replace(a)
            for a in self.datos.values()
            if (estanque_id is None or a.estanque_id == estanque_id)
            and (estado is None or a.estado == estado)
        ]
        res.sort(key=lambda a: (a.creada_en, a.id), reverse=True)
        return res[:limite] if limite else res


class NotificadorFalso:
    def __init__(self) -> None:
        self.enviadas = []

    def notificar(self, alerta) -> None:
        self.enviadas.append(alerta)
