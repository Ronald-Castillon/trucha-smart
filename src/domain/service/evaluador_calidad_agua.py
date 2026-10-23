"""Evalúa una lectura contra los umbrales estandarizados (RF-04)."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.model.lectura_agua import LecturaAgua, Parametro
from src.domain.model.umbral import ConjuntoUmbrales, Nivel


@dataclass(frozen=True)
class Evaluacion:
    parametro: Parametro
    valor: float
    nivel: Nivel
    mensaje: str

    @property
    def requiere_alerta(self) -> bool:
        return self.nivel is not Nivel.NORMAL


class EvaluadorCalidadAgua:
    def __init__(self, umbrales: ConjuntoUmbrales) -> None:
        self._umbrales = umbrales

    def evaluar(self, lectura: LecturaAgua) -> list[Evaluacion]:
        """Una evaluación por parámetro, en el orden temperatura, oxígeno, pH."""
        resultado = []
        for parametro, valor in lectura.valores().items():
            umbral = self._umbrales.de(parametro)
            nivel = umbral.clasificar(valor)
            resultado.append(Evaluacion(parametro, valor, nivel, umbral.describir(valor, nivel)))
        return resultado

    def niveles(self, lectura: LecturaAgua) -> dict[Parametro, Nivel]:
        return {e.parametro: e.nivel for e in self.evaluar(lectura)}
