"""Adaptadores de los puertos RepositorioAlimentacion y RepositorioMortalidad con SQLAlchemy."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.adapters.outbound.persistence.orm import RegistroAlimentacionORM, RegistroMortalidadORM
from src.domain.model.registro_alimentacion import RegistroAlimentacion
from src.domain.model.registro_mortalidad import RegistroMortalidad


def _alimentacion(f: RegistroAlimentacionORM) -> RegistroAlimentacion:
    return RegistroAlimentacion(
        id=f.id,
        lote_id=f.lote_id,
        cantidad_kg=f.cantidad_kg,
        registrado_por=f.registrado_por,
        registrado_en=f.registrado_en,
    )


def _mortalidad(f: RegistroMortalidadORM) -> RegistroMortalidad:
    return RegistroMortalidad(
        id=f.id,
        lote_id=f.lote_id,
        cantidad=f.cantidad,
        causa=f.causa,
        registrado_por=f.registrado_por,
        registrado_en=f.registrado_en,
    )


def _filtrar(consulta, modelo, lote_id, desde, hasta):
    consulta = consulta.where(modelo.lote_id == lote_id)
    if desde is not None:
        consulta = consulta.where(modelo.registrado_en >= desde)
    if hasta is not None:
        consulta = consulta.where(modelo.registrado_en <= hasta)
    return consulta.order_by(modelo.registrado_en.desc(), modelo.id.desc())


class RepositorioAlimentacionSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, r: RegistroAlimentacion) -> RegistroAlimentacion:
        fila = RegistroAlimentacionORM(
            lote_id=r.lote_id,
            cantidad_kg=r.cantidad_kg,
            registrado_por=r.registrado_por,
            registrado_en=r.registrado_en,
        )
        self._s.add(fila)
        self._s.flush()
        return _alimentacion(fila)

    def de_lote(
        self, lote_id: int, desde: datetime | None = None, hasta: datetime | None = None
    ) -> list[RegistroAlimentacion]:
        consulta = _filtrar(
            select(RegistroAlimentacionORM), RegistroAlimentacionORM, lote_id, desde, hasta
        )
        return [_alimentacion(f) for f in self._s.scalars(consulta)]

    def total_kg(self, lote_id: int) -> float:
        total = self._s.scalar(
            select(func.coalesce(func.sum(RegistroAlimentacionORM.cantidad_kg), 0)).where(
                RegistroAlimentacionORM.lote_id == lote_id
            )
        )
        return float(total or 0)


class RepositorioMortalidadSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, r: RegistroMortalidad) -> RegistroMortalidad:
        fila = RegistroMortalidadORM(
            lote_id=r.lote_id,
            cantidad=r.cantidad,
            causa=r.causa,
            registrado_por=r.registrado_por,
            registrado_en=r.registrado_en,
        )
        self._s.add(fila)
        self._s.flush()
        return _mortalidad(fila)

    def de_lote(
        self, lote_id: int, desde: datetime | None = None, hasta: datetime | None = None
    ) -> list[RegistroMortalidad]:
        consulta = _filtrar(
            select(RegistroMortalidadORM), RegistroMortalidadORM, lote_id, desde, hasta
        )
        return [_mortalidad(f) for f in self._s.scalars(consulta)]

    def total(self, lote_id: int) -> int:
        total = self._s.scalar(
            select(func.coalesce(func.sum(RegistroMortalidadORM.cantidad), 0)).where(
                RegistroMortalidadORM.lote_id == lote_id
            )
        )
        return int(total or 0)
