"""Adaptador del puerto RepositorioLectura con SQLAlchemy."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.outbound.persistence.orm import LecturaAguaORM
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua


def _a_dominio(f: LecturaAguaORM) -> LecturaAgua:
    return LecturaAgua(
        id=f.id,
        estanque_id=f.estanque_id,
        temperatura_c=f.temperatura_c,
        oxigeno_mg_l=f.oxigeno_mg_l,
        ph=f.ph,
        fuente=FuenteLectura(f.fuente),
        registrado_por=f.registrado_por,
        medido_en=f.medido_en,
    )


class RepositorioLecturaSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, lec: LecturaAgua) -> LecturaAgua:
        fila = LecturaAguaORM(
            estanque_id=lec.estanque_id,
            temperatura_c=lec.temperatura_c,
            oxigeno_mg_l=lec.oxigeno_mg_l,
            ph=lec.ph,
            fuente=lec.fuente.value,
            registrado_por=lec.registrado_por,
            medido_en=lec.medido_en,
        )
        self._s.add(fila)
        self._s.flush()
        return _a_dominio(fila)

    def ultima_de(self, estanque_id: int) -> LecturaAgua | None:
        fila = self._s.scalar(
            select(LecturaAguaORM)
            .where(LecturaAguaORM.estanque_id == estanque_id)
            .order_by(LecturaAguaORM.medido_en.desc(), LecturaAguaORM.id.desc())
            .limit(1)
        )
        return _a_dominio(fila) if fila else None

    def de_estanque(
        self,
        estanque_id: int,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        limite: int | None = None,
    ) -> list[LecturaAgua]:
        consulta = select(LecturaAguaORM).where(LecturaAguaORM.estanque_id == estanque_id)
        if desde is not None:
            consulta = consulta.where(LecturaAguaORM.medido_en >= desde)
        if hasta is not None:
            consulta = consulta.where(LecturaAguaORM.medido_en <= hasta)
        consulta = consulta.order_by(LecturaAguaORM.medido_en.desc(), LecturaAguaORM.id.desc())
        if limite is not None:
            consulta = consulta.limit(limite)
        return [_a_dominio(f) for f in self._s.scalars(consulta)]
