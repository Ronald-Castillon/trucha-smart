"""Adaptador del puerto RepositorioClaveIntegracion con SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.outbound.persistence.orm import ClaveIntegracionORM
from src.domain.model.clave_integracion import ClaveIntegracion


def _a_dominio(f: ClaveIntegracionORM) -> ClaveIntegracion:
    return ClaveIntegracion(
        id=f.id,
        nombre=f.nombre,
        prefijo=f.prefijo,
        hash_clave=f.hash_clave,
        creada_en=f.creada_en,
        creada_por=f.creada_por,
        activa=f.activa,
        ultimo_uso=f.ultimo_uso,
    )


class RepositorioClaveIntegracionSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, c: ClaveIntegracion) -> ClaveIntegracion:
        fila = self._s.get(ClaveIntegracionORM, c.id) if c.id else None
        if fila is None:
            fila = ClaveIntegracionORM()
            self._s.add(fila)
        fila.nombre, fila.prefijo, fila.hash_clave = c.nombre, c.prefijo, c.hash_clave
        fila.creada_en, fila.creada_por = c.creada_en, c.creada_por
        fila.activa, fila.ultimo_uso = c.activa, c.ultimo_uso
        self._s.flush()
        return _a_dominio(fila)

    def por_id(self, clave_id: int) -> ClaveIntegracion | None:
        fila = self._s.get(ClaveIntegracionORM, clave_id)
        return _a_dominio(fila) if fila else None

    def por_hash(self, hash_clave: str) -> ClaveIntegracion | None:
        fila = self._s.scalar(
            select(ClaveIntegracionORM).where(ClaveIntegracionORM.hash_clave == hash_clave)
        )
        return _a_dominio(fila) if fila else None

    def listar(self) -> list[ClaveIntegracion]:
        consulta = select(ClaveIntegracionORM).order_by(ClaveIntegracionORM.id.desc())
        return [_a_dominio(f) for f in self._s.scalars(consulta)]
