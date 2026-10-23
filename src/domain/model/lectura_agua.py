"""Lectura de calidad de agua (RF-03, brecha B-02)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.domain.errores import ErrorValidacion


class Parametro(StrEnum):
    TEMPERATURA = "TEMPERATURA"
    OXIGENO_DISUELTO = "OXIGENO_DISUELTO"
    PH = "PH"


class FuenteLectura(StrEnum):
    MANUAL = "MANUAL"
    SENSOR = "SENSOR"


# Límites físicos: fuera de ellos el dato es imposible (error de sensor o de digitación),
# no una condición del agua. No confundir con los umbrales de calidad (config/umbrales.yaml).
LIMITES_FISICOS: dict[Parametro, tuple[float, float]] = {
    Parametro.TEMPERATURA: (0.0, 40.0),
    Parametro.OXIGENO_DISUELTO: (0.0, math.inf),
    Parametro.PH: (0.0, 14.0),
}
CAMPOS = {
    Parametro.TEMPERATURA: ("temperatura_c", "La temperatura", "°C"),
    Parametro.OXIGENO_DISUELTO: ("oxigeno_mg_l", "El oxígeno disuelto", "mg/L"),
    Parametro.PH: ("ph", "El pH", ""),
}


def validar_fisicamente(parametro: Parametro, valor: float) -> None:
    campo, nombre, unidad = CAMPOS[parametro]
    minimo, maximo = LIMITES_FISICOS[parametro]
    if valor is None or not isinstance(valor, int | float) or math.isnan(valor):
        raise ErrorValidacion(campo, f"{nombre} es obligatorio y debe ser numérico")
    if not (minimo <= valor <= maximo):
        rango = f">= {minimo:g}" if maximo == math.inf else f"entre {minimo:g} y {maximo:g}"
        raise ErrorValidacion(
            campo,
            f"{nombre} {valor:g} {unidad} es físicamente imposible (debe estar {rango})".replace(
                "  ", " "
            ),
        )


@dataclass
class LecturaAgua:
    estanque_id: int
    temperatura_c: float
    oxigeno_mg_l: float
    ph: float
    fuente: FuenteLectura
    medido_en: datetime
    registrado_por: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        for parametro, valor in self.valores().items():
            validar_fisicamente(parametro, valor)

    def valores(self) -> dict[Parametro, float]:
        return {
            Parametro.TEMPERATURA: self.temperatura_c,
            Parametro.OXIGENO_DISUELTO: self.oxigeno_mg_l,
            Parametro.PH: self.ph,
        }
