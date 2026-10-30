"""Puerto de entrada: consulta de la bitácora de seguridad (RF-11)."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.evento_seguridad import EventoSeguridad
from src.domain.model.usuario import Usuario


class ConsultarAuditoria(Protocol):
    def listar(self, solicitante: Usuario, limite: int = 200) -> list[EventoSeguridad]: ...
