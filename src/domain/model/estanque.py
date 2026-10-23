"""Estanque o jaula de cultivo (RF-02, brecha B-01)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.domain.errores import ErrorValidacion


class TipoEstanque(StrEnum):
    ESTANQUE = "ESTANQUE"
    JAULA = "JAULA"


@dataclass
class Estanque:
    nombre: str
    tipo: TipoEstanque
    creado_en: datetime
    volumen_m3: float | None = None
    ubicacion: str | None = None
    activo: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip()
        if not (1 <= len(self.nombre) <= 80):
            raise ErrorValidacion("nombre", "El nombre del estanque es obligatorio (máx. 80)")
        if self.volumen_m3 is not None and self.volumen_m3 <= 0:
            raise ErrorValidacion("volumen_m3", "El volumen debe ser mayor que 0 m³")
        if self.ubicacion is not None:
            self.ubicacion = self.ubicacion.strip() or None
