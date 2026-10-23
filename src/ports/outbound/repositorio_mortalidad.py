"""Puerto de salida: persistencia de registros de mortalidad."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from src.domain.model.registro_mortalidad import RegistroMortalidad


class RepositorioMortalidad(Protocol):
    def guardar(self, registro: RegistroMortalidad) -> RegistroMortalidad: ...

    def de_lote(
        self, lote_id: int, desde: datetime | None = None, hasta: datetime | None = None
    ) -> list[RegistroMortalidad]:
        """Registros del lote en [desde, hasta], del más reciente al más antiguo."""
        ...

    def total(self, lote_id: int) -> int: ...
