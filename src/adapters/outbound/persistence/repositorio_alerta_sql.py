"""Adaptador del puerto RepositorioAlerta con SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.outbound.persistence.orm import AlertaORM
from src.domain.model.alerta import Alerta, EstadoAlerta
from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import Nivel


def _a_dominio(f: AlertaORM) -> Alerta:
    return Alerta(
        id=f.id,
        estanque_id=f.estanque_id,
        lectura_id=f.lectura_id,
        parametro=Parametro(f.parametro),
        nivel=Nivel(f.nivel),
        valor=f.valor,
        mensaje=f.mensaje,
        estado=EstadoAlerta(f.estado),
        creada_en=f.creada_en,
        atendida_por=f.atendida_por,
        atendida_en=f.atendida_en,
        observacion=f.observacion,
    )


class RepositorioAlertaSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, a: Alerta) -> Alerta:
        fila = self._s.get(AlertaORM, a.id) if a.id else None
        if fila is None:
            fila = AlertaORM()
            self._s.add(fila)
        fila.estanque_id, fila.lectura_id = a.estanque_id, a.lectura_id
        fila.parametro, fila.nivel = a.parametro.value, a.nivel.value
        fila.valor, fila.mensaje, fila.estado = a.valor, a.mensaje, a.estado.value
        fila.creada_en = a.creada_en
        fila.atendida_por, fila.atendida_en = a.atendida_por, a.atendida_en
        fila.observacion = a.observacion
        self._s.flush()
        return _a_dominio(fila)

    def por_id(self, alerta_id: int) -> Alerta | None:
        fila = self._s.get(AlertaORM, alerta_id)
        return _a_dominio(fila) if fila else None

    def abierta(self, estanque_id: int, parametro: Parametro, nivel: Nivel) -> Alerta | None:
        fila = self._s.scalar(
            select(AlertaORM)
            .where(
                AlertaORM.estanque_id == estanque_id,
                AlertaORM.parametro == parametro.value,
                AlertaORM.nivel == nivel.value,
                AlertaORM.estado == EstadoAlerta.ABIERTA.value,
            )
            .limit(1)
        )
        return _a_dominio(fila) if fila else None

    def listar(
        self,
        estanque_id: int | None = None,
        estado: EstadoAlerta | None = None,
        limite: int | None = None,
    ) -> list[Alerta]:
        consulta = select(AlertaORM)
        if estanque_id is not None:
            consulta = consulta.where(AlertaORM.estanque_id == estanque_id)
        if estado is not None:
            consulta = consulta.where(AlertaORM.estado == estado.value)
        consulta = consulta.order_by(AlertaORM.creada_en.desc(), AlertaORM.id.desc())
        if limite is not None:
            consulta = consulta.limit(limite)
        return [_a_dominio(f) for f in self._s.scalars(consulta)]
