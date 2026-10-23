"""Registro de peces muertos en un lote (RF-06)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.errores import ErrorValidacion


@dataclass
class RegistroMortalidad:
    lote_id: int
    cantidad: int
    registrado_en: datetime
    causa: str | None = None
    registrado_por: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.cantidad, int) or isinstance(self.cantidad, bool):
            raise ErrorValidacion("cantidad", "La mortalidad debe ser un número entero de peces")
        if self.cantidad <= 0:
            raise ErrorValidacion("cantidad", "La mortalidad debe ser mayor que 0 peces")
        self.causa = (self.causa or "").strip() or None
        if self.causa and len(self.causa) > 120:
            raise ErrorValidacion("causa", "La causa admite máximo 120 caracteres")
