"""Puerto de salida: modelo entrenado que estima la probabilidad de evento crítico (RF-12)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ResultadoModelo:
    probabilidad: float
    aportes: dict[str, float]  # contribución de cada característica a la predicción


class ModeloRiesgo(Protocol):
    @property
    def version(self) -> str: ...

    def predecir(self, x: dict[str, float]) -> ResultadoModelo: ...
