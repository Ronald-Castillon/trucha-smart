"""Puerto de entrada: consulta y atención de alertas (RF-04, brecha B-06)."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.alerta import Alerta, EstadoAlerta
from src.domain.model.usuario import Usuario


class AtenderAlerta(Protocol):
    def atender(self, alerta_id: int, observacion: str | None, solicitante: Usuario) -> Alerta:
        """Marca la alerta como ATENDIDA registrando usuario y fecha/hora."""
        ...

    def listar(
        self,
        solicitante: Usuario,
        estanque_id: int | None = None,
        estado: EstadoAlerta | None = None,
        limite: int = 100,
    ) -> list[Alerta]: ...
