"""Puerto de entrada: historial de lecturas, tendencias e índice de riesgo (RF-05)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from src.domain.model.estanque import Estanque
from src.domain.model.lectura_agua import LecturaAgua, Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Usuario
from src.domain.service.indice_riesgo import IndiceRiesgo


@dataclass(frozen=True)
class LecturaEvaluada:
    lectura: LecturaAgua
    niveles: dict[Parametro, Nivel]


@dataclass(frozen=True)
class Estadistica:
    minimo: float
    maximo: float
    promedio: float


@dataclass(frozen=True)
class Historial:
    estanque: Estanque
    desde: date
    hasta: date
    lecturas: list[LecturaEvaluada]  # de la más antigua a la más reciente
    estadisticas: dict[Parametro, Estadistica]


class ConsultarHistorial(Protocol):
    def historial(
        self,
        estanque_id: int,
        solicitante: Usuario,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> Historial:
        """Lecturas en [desde 00:00, hasta 23:59:59] UTC. Por defecto, los últimos 7 días."""
        ...

    def riesgo(self, estanque_id: int, solicitante: Usuario) -> IndiceRiesgo: ...
