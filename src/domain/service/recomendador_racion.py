"""Recomendación de ración diaria (RF-07, brecha B-08).

  ración (kg/día) = biomasa (kg) x tasa de alimentación (% biomasa/día según peso medio)
                    x factor de temperatura x factor de oxígeno
La tabla y los factores vienen de config/alimentacion.yaml (ADR-005). Un factor 0 (nivel
CRÍTICO) significa suspender la alimentación. La recomendación siempre muestra la regla
aplicada; la decisión final es del piscicultor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.errores import ErrorValidacion
from src.domain.model.umbral import NOMBRES_NIVEL, Nivel


@dataclass(frozen=True)
class TramoTasa:
    desde_g: float
    hasta_g: float | None  # None = sin límite superior
    tasa_pct: float

    def contiene(self, peso_g: float) -> bool:
        return peso_g >= self.desde_g and (self.hasta_g is None or peso_g < self.hasta_g)

    @property
    def descripcion(self) -> str:
        if self.hasta_g is None:
            return f">= {self.desde_g:g} g"
        if self.desde_g == 0:
            return f"< {self.hasta_g:g} g"
        return f"{self.desde_g:g}–{self.hasta_g:g} g"


@dataclass(frozen=True)
class TablaAlimentacion:
    tramos: tuple[TramoTasa, ...]
    factor_temperatura: dict[Nivel, float] = field(hash=False)
    factor_oxigeno: dict[Nivel, float] = field(hash=False)

    def __post_init__(self) -> None:
        if not self.tramos or self.tramos[0].desde_g != 0:
            raise ErrorValidacion("tasas", "La tabla de alimentación debe empezar en 0 g")
        for previo, siguiente in zip(self.tramos, self.tramos[1:], strict=False):
            if previo.hasta_g != siguiente.desde_g:
                raise ErrorValidacion("tasas", "Los tramos de peso deben ser contiguos")
        if self.tramos[-1].hasta_g is not None:
            raise ErrorValidacion("tasas", "El último tramo debe no tener límite superior")
        for t in self.tramos:
            if t.tasa_pct <= 0:
                raise ErrorValidacion("tasas", "Las tasas de alimentación deben ser > 0 %")
        for nombre, factores in (
            ("factor_temperatura", self.factor_temperatura),
            ("factor_oxigeno", self.factor_oxigeno),
        ):
            if set(factores) != set(Nivel):
                raise ErrorValidacion(nombre, f"{nombre} debe definir normal, precaucion y critica")
            if any(not 0 <= f <= 1 for f in factores.values()):
                raise ErrorValidacion(nombre, f"{nombre} debe estar entre 0 y 1")

    def tramo_para(self, peso_g: float) -> TramoTasa:
        return next(t for t in self.tramos if t.contiene(peso_g))


@dataclass(frozen=True)
class Recomendacion:
    biomasa_kg: float
    peso_medio_g: float
    tasa_pct: float
    tramo: str
    nivel_temperatura: Nivel | None
    nivel_oxigeno: Nivel | None
    factor_temperatura: float
    factor_oxigeno: float
    racion_kg: float
    suspender: bool
    regla: str
    advertencias: tuple[str, ...] = ()


class RecomendadorRacion:
    def __init__(self, tabla: TablaAlimentacion) -> None:
        self._tabla = tabla

    def recomendar(
        self,
        biomasa_kg: float,
        peso_medio_g: float,
        nivel_temperatura: Nivel | None,
        nivel_oxigeno: Nivel | None,
    ) -> Recomendacion:
        if biomasa_kg < 0:
            raise ErrorValidacion("biomasa_kg", "La biomasa no puede ser negativa")
        if peso_medio_g <= 0:
            raise ErrorValidacion("peso_medio_g", "El peso medio debe ser mayor que 0")
        advertencias = []
        if nivel_temperatura is None or nivel_oxigeno is None:
            advertencias.append(
                "Sin lectura de calidad de agua: se asumen factores normales; "
                "mida temperatura y oxígeno antes de alimentar"
            )
        n_t = nivel_temperatura or Nivel.NORMAL
        n_o = nivel_oxigeno or Nivel.NORMAL
        tramo = self._tabla.tramo_para(peso_medio_g)
        f_t = self._tabla.factor_temperatura[n_t]
        f_o = self._tabla.factor_oxigeno[n_o]
        racion = round(biomasa_kg * tramo.tasa_pct / 100 * f_t * f_o, 3)
        suspender = f_t == 0 or f_o == 0
        regla = (
            f"Ración = {biomasa_kg:.3f} kg de biomasa × {tramo.tasa_pct:g} % "
            f"(peso medio {peso_medio_g:g} g, tramo {tramo.descripcion}) "
            f"× {f_t:g} (temperatura {NOMBRES_NIVEL[n_t]}) "
            f"× {f_o:g} (oxígeno {NOMBRES_NIVEL[n_o]}) = {racion:.3f} kg/día"
        )
        if suspender:
            motivos = [
                nombre
                for nombre, nivel in (("temperatura", n_t), ("oxígeno disuelto", n_o))
                if nivel is Nivel.CRITICA
            ]
            regla = f"Suspender alimentación: {' y '.join(motivos)} en nivel CRÍTICO. " + regla
        return Recomendacion(
            biomasa_kg=biomasa_kg,
            peso_medio_g=peso_medio_g,
            tasa_pct=tramo.tasa_pct,
            tramo=tramo.descripcion,
            nivel_temperatura=nivel_temperatura,
            nivel_oxigeno=nivel_oxigeno,
            factor_temperatura=f_t,
            factor_oxigeno=f_o,
            racion_kg=racion,
            suspender=suspender,
            regla=regla,
            advertencias=tuple(advertencias),
        )
