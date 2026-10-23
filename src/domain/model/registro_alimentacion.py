"""Registro de alimento suministrado a un lote (RF-06, brecha B-08)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from src.domain.errores import ErrorValidacion

MAXIMO_KG_POR_REGISTRO = 10_000.0


@dataclass
class RegistroAlimentacion:
    lote_id: int
    cantidad_kg: float
    registrado_en: datetime
    registrado_por: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if (
            self.cantidad_kg is None
            or not isinstance(self.cantidad_kg, int | float)
            or math.isnan(self.cantidad_kg)
            or self.cantidad_kg <= 0
        ):
            raise ErrorValidacion("cantidad_kg", "La cantidad de alimento debe ser mayor que 0 kg")
        if self.cantidad_kg > MAXIMO_KG_POR_REGISTRO:
            raise ErrorValidacion(
                "cantidad_kg",
                f"La cantidad de alimento no puede superar {MAXIMO_KG_POR_REGISTRO:g} kg "
                "por registro",
            )
