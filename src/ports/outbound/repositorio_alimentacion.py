"""Puerto de salida: persistencia de registros de alimentación."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from src.domain.model.registro_alimentacion import RegistroAlimentacion


class RepositorioAlimentacion(Protocol):
    def guardar(self, registro: RegistroAlimentacion) -> RegistroAlimentacion: ...

    def de_lote(
        self, lote_id: int, desde: datetime | None = None, hasta: datetime | None = None
    ) -> list[RegistroAlimentacion]:
        """Registros del lote en [desde, hasta], del más reciente al más antiguo."""
        ...

    def total_kg(self, lote_id: int) -> float: ...
