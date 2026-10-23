"""Biomasa y factor de conversión alimenticia (FCR) de un lote (RF-06, brecha B-08).

  peces vivos      = peces sembrados - mortalidad acumulada
  biomasa (kg)     = peces vivos x peso medio actual (g) / 1000
  ganancia (kg)    = biomasa actual - biomasa inicial (peces sembrados x peso medio inicial)
  FCR              = alimento total suministrado (kg) / ganancia de biomasa (kg)
Si la ganancia es 0 (o negativa) el FCR es "no calculable": no se divide ni se lanza error.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.errores import ErrorValidacion
from src.domain.model.lote import Lote

NO_CALCULABLE = "no calculable"


@dataclass(frozen=True)
class ResumenProduccion:
    lote_id: int
    codigo: str
    peces_sembrados: int
    mortalidad_total: int
    peces_vivos: int
    supervivencia_pct: float
    peso_medio_inicial_g: float
    peso_medio_actual_g: float
    biomasa_inicial_kg: float
    biomasa_kg: float
    ganancia_biomasa_kg: float
    alimento_total_kg: float
    fcr: float | None
    fcr_detalle: str

    @property
    def fcr_texto(self) -> str:
        return NO_CALCULABLE if self.fcr is None else f"{self.fcr:.2f}"


def peces_vivos(lote: Lote, mortalidad_total: int) -> int:
    if mortalidad_total < 0:
        raise ErrorValidacion("cantidad", "La mortalidad acumulada no puede ser negativa")
    if mortalidad_total > lote.num_peces_inicial:
        raise ErrorValidacion(
            "cantidad",
            f"La mortalidad acumulada ({mortalidad_total}) supera los peces sembrados "
            f"({lote.num_peces_inicial})",
        )
    return lote.num_peces_inicial - mortalidad_total


def biomasa_kg(peces: int, peso_medio_g: float) -> float:
    return round(peces * peso_medio_g / 1000, 3)


def calcular_fcr(alimento_total_kg: float, ganancia_kg: float) -> tuple[float | None, str]:
    """Devuelve (FCR, explicación). FCR es None cuando no es calculable."""
    if alimento_total_kg < 0:
        raise ErrorValidacion("cantidad_kg", "El alimento total no puede ser negativo")
    if ganancia_kg == 0:
        return None, "No calculable: la ganancia de biomasa es 0 kg"
    if ganancia_kg < 0:
        return None, f"No calculable: la biomasa disminuyó {abs(ganancia_kg):.3f} kg"
    fcr = round(alimento_total_kg / ganancia_kg, 2)
    return fcr, (
        f"FCR = {alimento_total_kg:.3f} kg de alimento / {ganancia_kg:.3f} kg de ganancia "
        f"= {fcr:.2f}"
    )


def resumen_produccion(
    lote: Lote, mortalidad_total: int, alimento_total_kg: float
) -> ResumenProduccion:
    vivos = peces_vivos(lote, mortalidad_total)
    inicial = biomasa_kg(lote.num_peces_inicial, lote.peso_medio_inicial_g)
    actual = biomasa_kg(vivos, lote.peso_medio_actual_g)
    ganancia = round(actual - inicial, 3)
    alimento = round(alimento_total_kg, 3)
    fcr, detalle = calcular_fcr(alimento, ganancia)
    return ResumenProduccion(
        lote_id=lote.id,
        codigo=lote.codigo,
        peces_sembrados=lote.num_peces_inicial,
        mortalidad_total=mortalidad_total,
        peces_vivos=vivos,
        supervivencia_pct=round(vivos / lote.num_peces_inicial * 100, 2),
        peso_medio_inicial_g=lote.peso_medio_inicial_g,
        peso_medio_actual_g=lote.peso_medio_actual_g,
        biomasa_inicial_kg=inicial,
        biomasa_kg=actual,
        ganancia_biomasa_kg=ganancia,
        alimento_total_kg=alimento,
        fcr=fcr,
        fcr_detalle=detalle,
    )
