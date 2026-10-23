"""Escenarios de lecturas simuladas para el sensor (ADR-004)."""

from __future__ import annotations

import math
import random
from collections.abc import Iterator
from dataclasses import dataclass

ESCENARIOS = ("normal", "critico_oxigeno", "critico_temperatura")


@dataclass(frozen=True)
class Medicion:
    temperatura_c: float
    oxigeno_mg_l: float
    ph: float


def _r(x: float) -> float:
    return round(x, 2)


def generar(escenario: str, semilla: int | None = None) -> Iterator[Medicion]:
    """Genera mediciones sucesivas del escenario indicado.

    - normal: valores dentro de los rangos normales con pequeña variación.
    - critico_oxigeno: el OD cae 0.4 mg/L por paso desde 8.0 hasta 3.5 (pasa por
      precaución y llega a crítico) y se mantiene allí.
    - critico_temperatura: la temperatura sube 0.5 °C por paso desde 14.0 hasta 20.0.
    """
    if escenario not in ESCENARIOS:
        raise ValueError(f"Escenario desconocido: {escenario}. Opciones: {', '.join(ESCENARIOS)}")
    rnd = random.Random(semilla)
    paso = 0
    while True:
        onda = math.sin(paso / 6)
        temperatura = 12.5 + 1.2 * onda + rnd.uniform(-0.2, 0.2)
        oxigeno = 8.3 - 0.4 * onda + rnd.uniform(-0.2, 0.2)
        ph = 7.3 + rnd.uniform(-0.2, 0.2)
        if escenario == "critico_oxigeno":
            oxigeno = max(3.5, 8.0 - 0.4 * paso)
        elif escenario == "critico_temperatura":
            temperatura = min(20.0, 14.0 + 0.5 * paso)
        yield Medicion(_r(temperatura), _r(oxigeno), _r(ph))
        paso += 1
