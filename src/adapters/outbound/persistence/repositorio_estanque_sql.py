"""Adaptadores de los puertos RepositorioEstanque y RepositorioLote con SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.outbound.persistence.orm import EstanqueORM, LoteORM
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lote import Lote


def _estanque(f: EstanqueORM) -> Estanque:
    return Estanque(
        id=f.id,
        nombre=f.nombre,
        tipo=TipoEstanque(f.tipo),
        volumen_m3=f.volumen_m3,
        ubicacion=f.ubicacion,
        activo=f.activo,
        creado_en=f.creado_en,
    )


def _lote(f: LoteORM) -> Lote:
    return Lote(
        id=f.id,
        estanque_id=f.estanque_id,
        codigo=f.codigo,
        num_peces_inicial=f.num_peces_inicial,
        peso_medio_inicial_g=f.peso_medio_inicial_g,
        peso_medio_actual_g=f.peso_medio_actual_g,
        fecha_siembra=f.fecha_siembra,
        activo=f.activo,
        fecha_cierre=f.fecha_cierre,
    )


class RepositorioEstanqueSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, e: Estanque) -> Estanque:
        fila = self._s.get(EstanqueORM, e.id) if e.id else None
        if fila is None:
            fila = EstanqueORM()
            self._s.add(fila)
        fila.nombre, fila.tipo = e.nombre, e.tipo.value
        fila.volumen_m3, fila.ubicacion = e.volumen_m3, e.ubicacion
        fila.activo, fila.creado_en = e.activo, e.creado_en
        self._s.flush()
        return _estanque(fila)

    def por_id(self, estanque_id: int) -> Estanque | None:
        fila = self._s.get(EstanqueORM, estanque_id)
        return _estanque(fila) if fila else None

    def por_nombre(self, nombre: str) -> Estanque | None:
        fila = self._s.scalar(select(EstanqueORM).where(EstanqueORM.nombre == nombre))
        return _estanque(fila) if fila else None

    def listar(self, solo_activos: bool = True) -> list[Estanque]:
        consulta = select(EstanqueORM).order_by(EstanqueORM.nombre)
        if solo_activos:
            consulta = consulta.where(EstanqueORM.activo.is_(True))
        return [_estanque(f) for f in self._s.scalars(consulta)]


class RepositorioLoteSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, lo: Lote) -> Lote:
        fila = self._s.get(LoteORM, lo.id) if lo.id else None
        if fila is None:
            fila = LoteORM()
            self._s.add(fila)
        fila.estanque_id, fila.codigo = lo.estanque_id, lo.codigo
        fila.num_peces_inicial = lo.num_peces_inicial
        fila.peso_medio_inicial_g = lo.peso_medio_inicial_g
        fila.peso_medio_actual_g = lo.peso_medio_actual_g
        fila.fecha_siembra, fila.activo, fila.fecha_cierre = (
            lo.fecha_siembra,
            lo.activo,
            lo.fecha_cierre,
        )
        self._s.flush()
        return _lote(fila)

    def por_id(self, lote_id: int) -> Lote | None:
        fila = self._s.get(LoteORM, lote_id)
        return _lote(fila) if fila else None

    def por_codigo(self, codigo: str) -> Lote | None:
        fila = self._s.scalar(select(LoteORM).where(LoteORM.codigo == codigo))
        return _lote(fila) if fila else None

    def activo_de(self, estanque_id: int) -> Lote | None:
        fila = self._s.scalar(
            select(LoteORM).where(LoteORM.estanque_id == estanque_id, LoteORM.activo.is_(True))
        )
        return _lote(fila) if fila else None

    def de_estanque(self, estanque_id: int) -> list[Lote]:
        consulta = (
            select(LoteORM)
            .where(LoteORM.estanque_id == estanque_id)
            .order_by(LoteORM.fecha_siembra.desc(), LoteORM.id.desc())
        )
        return [_lote(f) for f in self._s.scalars(consulta)]
