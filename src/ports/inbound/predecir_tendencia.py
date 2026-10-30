"""Puerto de entrada: predicción de tendencia de calidad de agua por estanque (RF-10)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.domain.model.estanque import Estanque
from src.domain.model.usuario import Usuario
from src.domain.service.predictor_tendencia import Prediccion


@dataclass(frozen=True)
class PrediccionEstanque:
    estanque: Estanque
    basada_en_hasta: datetime | None  # momento de la última lectura usada
    predicciones: list[Prediccion]
    principal: Prediccion | None  # la más urgente (crítico o riesgo más cercano)


class PredecirTendencia(Protocol):
    def predecir(self, estanque_id: int, solicitante: Usuario) -> PrediccionEstanque: ...
