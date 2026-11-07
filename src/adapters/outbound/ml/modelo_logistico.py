"""Adaptador del puerto ModeloRiesgo: regresión logística exportada a JSON (ADR-007).

El entrenamiento (tools/entrenar_modelo_riesgo.py, scikit-learn) exporta medias, escalas,
coeficientes e intercepto; aquí solo se evalúa la fórmula. No se usa pickle: cargar un archivo
de modelo nunca ejecuta código.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from src.ports.outbound.modelo_riesgo import ResultadoModelo


class ModeloLogistico:
    def __init__(self, datos: dict) -> None:
        self._version = datos["version"]
        self._caracteristicas = list(datos["caracteristicas"])
        self._media = [float(v) for v in datos["media"]]
        self._escala = [float(v) or 1.0 for v in datos["escala"]]
        self._coef = [float(v) for v in datos["coeficientes"]]
        self._intercepto = float(datos["intercepto"])
        if not (
            len(self._caracteristicas) == len(self._media) == len(self._escala) == len(self._coef)
        ):
            raise ValueError("El archivo del modelo tiene vectores de distinto tamaño")

    @classmethod
    def desde_archivo(cls, ruta: Path) -> ModeloLogistico:
        return cls(json.loads(Path(ruta).read_text(encoding="utf-8")))

    @property
    def version(self) -> str:
        return self._version

    def predecir(self, x: dict[str, float]) -> ResultadoModelo:
        aportes = {
            nombre: coef * (x[nombre] - media) / escala
            for nombre, media, escala, coef in zip(
                self._caracteristicas, self._media, self._escala, self._coef, strict=True
            )
        }
        z = self._intercepto + sum(aportes.values())
        probabilidad = 1 / (1 + math.exp(-z)) if z > -700 else 0.0
        return ResultadoModelo(probabilidad, aportes)
