"""Umbrales de calidad de agua estandarizados (RF-04, brecha B-05).

Los valores vienen de config/umbrales.yaml (ADR-005); el dominio solo define la regla:
  - dentro de [normal_min, normal_max]          -> NORMAL
  - fuera de normal pero en [prec_min, prec_max] -> PRECAUCION
  - fuera del rango de precaución                -> CRITICA
Límites inclusivos; None significa "sin límite" en esa dirección.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.domain.errores import ErrorValidacion
from src.domain.model.lectura_agua import Parametro


class Nivel(StrEnum):
    NORMAL = "NORMAL"
    PRECAUCION = "PRECAUCION"
    CRITICA = "CRITICA"


NOMBRES_PARAMETRO = {
    Parametro.TEMPERATURA: "Temperatura",
    Parametro.OXIGENO_DISUELTO: "Oxígeno disuelto",
    Parametro.PH: "pH",
}
NOMBRES_NIVEL = {Nivel.NORMAL: "normal", Nivel.PRECAUCION: "PRECAUCIÓN", Nivel.CRITICA: "CRÍTICA"}


def _dentro(valor: float, minimo: float | None, maximo: float | None) -> bool:
    return (minimo is None or valor >= minimo) and (maximo is None or valor <= maximo)


def _rango(minimo: float | None, maximo: float | None) -> str:
    if minimo is None and maximo is None:
        return "cualquier valor"
    if minimo is None:
        return f"<= {maximo:g}"
    if maximo is None:
        return f">= {minimo:g}"
    return f"{minimo:g}–{maximo:g}"


@dataclass(frozen=True)
class Umbral:
    parametro: Parametro
    unidad: str
    normal_min: float | None
    normal_max: float | None
    precaucion_min: float | None
    precaucion_max: float | None

    def __post_init__(self) -> None:
        def contiene(exterior: float | None, interior: float | None, es_min: bool) -> bool:
            if exterior is None:
                return True
            if interior is None:
                return False
            return exterior <= interior if es_min else exterior >= interior

        if not (
            contiene(self.precaucion_min, self.normal_min, True)
            and contiene(self.precaucion_max, self.normal_max, False)
        ):
            raise ErrorValidacion(
                self.parametro.value.lower(),
                f"Umbral inválido para {self.parametro.value}: el rango de precaución "
                "debe contener al rango normal",
            )
        for a, b in (
            (self.normal_min, self.normal_max),
            (self.precaucion_min, self.precaucion_max),
        ):
            if a is not None and b is not None and a > b:
                raise ErrorValidacion(
                    self.parametro.value.lower(),
                    f"Umbral inválido para {self.parametro.value}: mínimo mayor que máximo",
                )

    def clasificar(self, valor: float) -> Nivel:
        if _dentro(valor, self.normal_min, self.normal_max):
            return Nivel.NORMAL
        if _dentro(valor, self.precaucion_min, self.precaucion_max):
            return Nivel.PRECAUCION
        return Nivel.CRITICA

    @property
    def rango_normal(self) -> str:
        return _rango(self.normal_min, self.normal_max)

    def describir(self, valor: float, nivel: Nivel) -> str:
        unidad = f" {self.unidad}" if self.unidad and self.unidad != "pH" else ""
        return (
            f"{NOMBRES_PARAMETRO[self.parametro]} en {NOMBRES_NIVEL[nivel]}: "
            f"{valor:.2f}{unidad} (normal {self.rango_normal}{unidad})"
        )


@dataclass(frozen=True)
class ConjuntoUmbrales:
    temperatura: Umbral
    oxigeno_disuelto: Umbral
    ph: Umbral

    def __post_init__(self) -> None:
        for p, u in self.por_parametro().items():
            if u.parametro is not p:
                raise ErrorValidacion(p.value.lower(), f"El umbral de {p.value} está mal asignado")

    def por_parametro(self) -> dict[Parametro, Umbral]:
        return {
            Parametro.TEMPERATURA: self.temperatura,
            Parametro.OXIGENO_DISUELTO: self.oxigeno_disuelto,
            Parametro.PH: self.ph,
        }

    def de(self, parametro: Parametro) -> Umbral:
        return self.por_parametro()[parametro]
