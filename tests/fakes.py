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
