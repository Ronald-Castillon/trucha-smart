"""Índice de riesgo de un estanque (RF-05, brecha B-07).

riesgo = min(100, 40 x parámetros CRÍTICOS en la última lectura
                  + 15 x parámetros en PRECAUCIÓN en la última lectura
                  + 10 x alertas CRÍTICAS abiertas)
Semáforo: 0-29 verde (bajo), 30-59 amarillo (medio), >= 60 rojo (alto).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import Nivel

PESO_CRITICO = 40
PESO_PRECAUCION = 15
PESO_ALERTA_CRITICA = 10
MAXIMO = 100
LIMITE_MEDIO = 30
LIMITE_ALTO = 60


class Semaforo(StrEnum):
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"


ETIQUETAS = {Semaforo.VERDE: "bajo", Semaforo.AMARILLO: "medio", Semaforo.ROJO: "alto"}


@dataclass(frozen=True)
class IndiceRiesgo:
    valor: int
    semaforo: Semaforo
    parametros_criticos: int
    parametros_precaucion: int
    alertas_criticas_abiertas: int

    @property
    def nivel(self) -> str:
        return ETIQUETAS[self.semaforo]

    @property
    def formula(self) -> str:
        bruto = (
            PESO_CRITICO * self.parametros_criticos
            + PESO_PRECAUCION * self.parametros_precaucion
            + PESO_ALERTA_CRITICA * self.alertas_criticas_abiertas
        )
        return (
            f"min(100, {PESO_CRITICO}×{self.parametros_criticos} + "
            f"{PESO_PRECAUCION}×{self.parametros_precaucion} + "
            f"{PESO_ALERTA_CRITICA}×{self.alertas_criticas_abiertas}) = min(100, {bruto}) "
            f"= {self.valor}"
        )


def semaforo_de(valor: int) -> Semaforo:
    if valor >= LIMITE_ALTO:
        return Semaforo.ROJO
    if valor >= LIMITE_MEDIO:
        return Semaforo.AMARILLO
    return Semaforo.VERDE


def calcular_indice_riesgo(
    niveles_ultima_lectura: dict[Parametro, Nivel], alertas_criticas_abiertas: int
) -> IndiceRiesgo:
    if alertas_criticas_abiertas < 0:
        raise ValueError("El número de alertas no puede ser negativo")
    criticos = sum(1 for n in niveles_ultima_lectura.values() if n is Nivel.CRITICA)
    precaucion = sum(1 for n in niveles_ultima_lectura.values() if n is Nivel.PRECAUCION)
    valor = min(
        MAXIMO,
        PESO_CRITICO * criticos
        + PESO_PRECAUCION * precaucion
        + PESO_ALERTA_CRITICA * alertas_criticas_abiertas,
    )
    return IndiceRiesgo(valor, semaforo_de(valor), criticos, precaucion, alertas_criticas_abiertas)
