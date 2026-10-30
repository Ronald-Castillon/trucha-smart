"""Adaptador del puerto RepositorioEventoSeguridad con SQLAlchemy (RF-11)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.outbound.persistence.orm import EventoSeguridadORM
from src.domain.model.evento_seguridad import EventoSeguridad, TipoEvento


def _a_dominio(f: EventoSeguridadORM) -> EventoSeguridad:
    return EventoSeguridad(
        id=f.id,
        tipo=TipoEvento(f.tipo),
        momento=f.momento,
        nombre_usuario=f.nombre_usuario,
        usuario_id=f.usuario_id,
        ip=f.ip,
        detalle=f.detalle,
    )


class RepositorioEventoSeguridadSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, e: EventoSeguridad) -> EventoSeguridad:
        fila = EventoSeguridadORM(
            tipo=e.tipo.value,
            momento=e.momento,
            nombre_usuario=e.nombre_usuario,
            usuario_id=e.usuario_id,
            ip=e.ip,
            detalle=e.detalle,
        )
        self._s.add(fila)
        self._s.flush()
        return _a_dominio(fila)

    def recientes(self, limite: int) -> list[EventoSeguridad]:
        consulta = (
            select(EventoSeguridadORM)
            .order_by(EventoSeguridadORM.momento.desc(), EventoSeguridadORM.id.desc())
            .limit(limite)
        )
        return [_a_dominio(f) for f in self._s.scalars(consulta)]
