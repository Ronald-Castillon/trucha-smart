"""Puerto de salida: bitácora de eventos de seguridad (RF-11)."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.evento_seguridad import EventoSeguridad


class RepositorioEventoSeguridad(Protocol):
    def guardar(self, evento: EventoSeguridad) -> EventoSeguridad: ...

    def recientes(self, limite: int) -> list[EventoSeguridad]:
        """Los últimos `limite` eventos, del más reciente al más antiguo."""
        ...
