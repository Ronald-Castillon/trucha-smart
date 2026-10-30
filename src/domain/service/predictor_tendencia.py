"""Predicción de tendencia de calidad de agua (RF-10, brecha B-10, ADR-006).

Método explicable: regresión lineal por mínimos cuadrados de cada parámetro sobre las lecturas
de las 24 h previas a la última lectura. Si la recta avanza hacia el límite crítico del umbral
(config/umbrales.yaml) y lo cruzaría dentro del horizonte (6 h), se informa en cuántas horas.
Solo se considera riesgo si el ajuste es significativo (R² >= 0.5), para no alarmar por ruido.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import NOMBRES_PARAMETRO, Umbral

MINIMO_PUNTOS = 4
HORIZONTE_HORAS = 6.0
R2_MINIMO = 0.5


class EstadoPrediccion(StrEnum):
    DATOS_INSUFICIENTES = "DATOS_INSUFICIENTES"
    SIN_RIESGO = "SIN_RIESGO"
    RIESGO = "RIESGO"
    YA_CRITICO = "YA_CRITICO"


@dataclass(frozen=True)
class Ajuste:
    pendiente_por_hora: float
    intercepto: float
    r2: float


@dataclass(frozen=True)
class Prediccion:
    parametro: Parametro
    estado: EstadoPrediccion
    puntos: int
    valor_actual: float | None
    pendiente_por_hora: float | None
    r2: float | None
    limite: float | None
    horas_hasta_limite: float | None
    momento_estimado: datetime | None
    mensaje: str


def ajustar(xs: list[float], ys: list[float]) -> Ajuste:
    """Mínimos cuadrados y = a + b·x. Con varianza nula en y, R² = 1 si la recta es exacta."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return Ajuste(0.0, my, 0.0)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / sxx
    a = my - b * mx
    sst = sum((y - my) ** 2 for y in ys)
    sse = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys, strict=True))
    r2 = 1.0 if sst == 0 else max(0.0, 1 - sse / sst)
    return Ajuste(b, a, r2)


def predecir(
    parametro: Parametro, serie: list[tuple[datetime, float]], umbral: Umbral
) -> Prediccion:
    """`serie`: (momento, valor) de las lecturas a considerar, en cualquier orden."""
    nombre = NOMBRES_PARAMETRO[parametro]
    serie = sorted(serie)
    if len(serie) < MINIMO_PUNTOS:
        mensaje = (
            f"{nombre}: datos insuficientes ({len(serie)} lecturas en 24 h; "
            f"se necesitan {MINIMO_PUNTOS})"
        )
        return Prediccion(
            parametro,
            EstadoPrediccion.DATOS_INSUFICIENTES,
            len(serie),
            None,
            None,
            None,
            None,
            None,
            None,
            mensaje,
        )
    ultimo_t, actual = serie[-1]
    xs = [(t - ultimo_t).total_seconds() / 3600 for t, _ in serie]
    ajuste = ajustar(xs, [v for _, v in serie])
    base = dict(
        parametro=parametro,
        puntos=len(serie),
        valor_actual=actual,
        pendiente_por_hora=round(ajuste.pendiente_por_hora, 4),
        r2=round(ajuste.r2, 3),
    )

    limites = []
    if umbral.precaucion_min is not None:
        limites.append((umbral.precaucion_min, -1))  # crítico por debajo
    if umbral.precaucion_max is not None:
        limites.append((umbral.precaucion_max, +1))  # crítico por encima
    for limite, sentido in limites:
        if (sentido < 0 and actual < limite) or (sentido > 0 and actual > limite):
            return Prediccion(
                **base,
                estado=EstadoPrediccion.YA_CRITICO,
                limite=limite,
                horas_hasta_limite=0.0,
                momento_estimado=ultimo_t,
                mensaje=f"{nombre} ya está en nivel crítico ({actual:g})",
            )

    b = ajuste.pendiente_por_hora
    for limite, sentido in limites:
        hacia_limite = (sentido < 0 and b < 0) or (sentido > 0 and b > 0)
        if not hacia_limite or ajuste.r2 < R2_MINIMO:
            continue
        horas = (limite - actual) / b  # proyección desde el último valor con la pendiente ajustada
        if 0 <= horas <= HORIZONTE_HORAS:
            momento = ultimo_t + timedelta(hours=horas)
            return Prediccion(
                **base,
                estado=EstadoPrediccion.RIESGO,
                limite=limite,
                horas_hasta_limite=round(horas, 2),
                momento_estimado=momento,
                mensaje=(
                    f"{nombre} alcanzaría el nivel crítico ({limite:g}) en ~{horas:.1f} h "
                    f"(hacia las {momento:%H:%M} UTC); tendencia {b:+.2f}/h, R² {ajuste.r2:.2f}"
                ),
            )
    return Prediccion(
        **base,
        estado=EstadoPrediccion.SIN_RIESGO,
        limite=None,
        horas_hasta_limite=None,
        momento_estimado=None,
        mensaje=(
            f"{nombre}: sin riesgo previsto en {HORIZONTE_HORAS:g} h "
            f"(tendencia {b:+.2f}/h, R² {ajuste.r2:.2f})"
        ),
    )
