"""Puerto de entrada: riesgo de evento crítico estimado por un modelo entrenado (RF-12)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.domain.model.estanque import Estanque
from src.domain.model.usuario import Usuario


@dataclass(frozen=True)
class Factor:
    nombre: str
    aporte: float  # contribución positiva al logit del modelo (mayor = empuja más al riesgo)


@dataclass(frozen=True)
class EvaluacionRiesgoModelo:
    estanque: Estanque
    nivel: str
    probabilidad: float | None
    factores: list[Factor]
    version_modelo: str
    puntos: int
    basada_en_hasta: datetime | None
    mensaje: str


class EvaluarRiesgoModelo(Protocol):
    def evaluar(self, estanque_id: int, solicitante: Usuario) -> EvaluacionRiesgoModelo: ...
