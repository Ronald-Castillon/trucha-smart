"""Riesgo de evento crítico estimado por un modelo entrenado (RF-12, Incremento 4, ADR-007).

El dominio no conoce el algoritmo: calcula las características de la ventana de 24 h previas a la
última lectura (las mismas que usa el entrenamiento, tools/entrenar_modelo_riesgo.py) y pide la
probabilidad al puerto de salida ModeloRiesgo. Un «evento crítico» es que el oxígeno disuelto baje
del límite de precaución o la temperatura supere el suyo (config/umbrales.yaml) en las próximas
6 horas.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum

from src.domain.errores import NoEncontrado
from src.domain.model.lectura_agua import LecturaAgua
from src.domain.model.umbral import ConjuntoUmbrales
from src.domain.model.usuario import Permiso, Usuario
from src.domain.service.predictor_tendencia import ajustar
from src.ports.inbound.evaluar_riesgo_modelo import EvaluacionRiesgoModelo, Factor
from src.ports.outbound.modelo_riesgo import ModeloRiesgo
from src.ports.outbound.repositorio_estanque import RepositorioEstanque
from src.ports.outbound.repositorio_lectura import RepositorioLectura

VENTANA = timedelta(hours=24)
VENTANA_TENDENCIA = timedelta(hours=6)
HORIZONTE_HORAS = 6
MINIMO_PUNTOS = 4
UMBRAL_MEDIO = 0.30
UMBRAL_ALTO = 0.60

# od_actual y t_actual no se usan como entrada: equivalen a los márgenes desplazados (colineales)
# y repartirían el peso entre dos columnas, lo que confunde la explicación de los factores.
CARACTERISTICAS = (
    "ph_actual",
    "od_pendiente_6h",
    "t_pendiente_6h",
    "od_min_24h",
    "t_max_24h",
    "od_margen",
    "t_margen",
)
NOMBRES = {
    "od_actual": "oxígeno disuelto actual",
    "t_actual": "temperatura actual",
    "ph_actual": "pH actual",
    "od_pendiente_6h": "tendencia del oxígeno (6 h)",
    "t_pendiente_6h": "tendencia de la temperatura (6 h)",
    "od_min_24h": "oxígeno mínimo de 24 h",
    "t_max_24h": "temperatura máxima de 24 h",
    "od_margen": "margen de oxígeno sobre el límite",
    "t_margen": "margen de temperatura bajo el límite",
}


class NivelRiesgoModelo(StrEnum):
    DATOS_INSUFICIENTES = "DATOS_INSUFICIENTES"
    YA_CRITICO = "YA_CRITICO"
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


def _pendiente(puntos: list[tuple[datetime, float]], fin: datetime) -> float:
    recientes = [(t, v) for t, v in puntos if t > fin - VENTANA_TENDENCIA]
    if len(recientes) < 2:
        return 0.0
    xs = [(t - fin).total_seconds() / 3600 for t, _ in recientes]
    return ajustar(xs, [v for _, v in recientes]).pendiente_por_hora


def caracteristicas(
    serie: list[tuple[datetime, float, float, float]], od_limite: float, t_limite: float
) -> dict[str, float] | None:
    """`serie`: (momento, temperatura, oxígeno, pH) de la ventana de 24 h, en cualquier orden.

    Devuelve None si hay menos de MINIMO_PUNTOS lecturas.
    """
    if len(serie) < MINIMO_PUNTOS:
        return None
    serie = sorted(serie)
    fin, t_act, od_act, ph_act = serie[-1]
    return {
        "od_actual": od_act,
        "t_actual": t_act,
        "ph_actual": ph_act,
        "od_pendiente_6h": _pendiente([(m, od) for m, _, od, _ in serie], fin),
        "t_pendiente_6h": _pendiente([(m, t) for m, t, _, _ in serie], fin),
        "od_min_24h": min(od for _, _, od, _ in serie),
        "t_max_24h": max(t for _, t, _, _ in serie),
        "od_margen": od_act - od_limite,
        "t_margen": t_limite - t_act,
    }


def nivel_de(probabilidad: float) -> NivelRiesgoModelo:
    if probabilidad >= UMBRAL_ALTO:
        return NivelRiesgoModelo.ALTO
    if probabilidad >= UMBRAL_MEDIO:
        return NivelRiesgoModelo.MEDIO
    return NivelRiesgoModelo.BAJO


class ServicioRiesgoModelo:
    """Implementa el puerto de entrada EvaluarRiesgoModelo."""

    def __init__(
        self,
        lecturas: RepositorioLectura,
        estanques: RepositorioEstanque,
        umbrales: ConjuntoUmbrales,
        modelo: ModeloRiesgo,
    ) -> None:
        self._lecturas = lecturas
        self._estanques = estanques
        self._umbrales = umbrales
        self._modelo = modelo

    def evaluar(self, estanque_id: int, solicitante: Usuario) -> EvaluacionRiesgoModelo:
        solicitante.exigir(Permiso.CONSULTAR)
        estanque = self._estanques.por_id(estanque_id)
        if estanque is None:
            raise NoEncontrado(f"No existe el estanque {estanque_id}")
        ultima = self._lecturas.ultima_de(estanque_id)
        lecturas: list[LecturaAgua] = (
            self._lecturas.de_estanque(estanque_id, ultima.medido_en - VENTANA, ultima.medido_en)
            if ultima
            else []
        )
        od_lim = self._umbrales.oxigeno_disuelto.precaucion_min
        t_lim = self._umbrales.temperatura.precaucion_max
        x = caracteristicas(
            [(x.medido_en, x.temperatura_c, x.oxigeno_mg_l, x.ph) for x in lecturas], od_lim, t_lim
        )
        base = dict(estanque=estanque, version_modelo=self._modelo.version, puntos=len(lecturas))
        if x is None:
            return EvaluacionRiesgoModelo(
                **base,
                nivel=NivelRiesgoModelo.DATOS_INSUFICIENTES,
                probabilidad=None,
                factores=[],
                basada_en_hasta=ultima.medido_en if ultima else None,
                mensaje=f"Datos insuficientes: {len(lecturas)} lecturas en 24 h "
                f"(se necesitan {MINIMO_PUNTOS})",
            )
        if x["od_margen"] < 0 or x["t_margen"] < 0:
            return EvaluacionRiesgoModelo(
                **base,
                nivel=NivelRiesgoModelo.YA_CRITICO,
                probabilidad=1.0,
                factores=[],
                basada_en_hasta=ultima.medido_en,
                mensaje="El estanque ya está en condición crítica: atender la alerta",
            )
        r = self._modelo.predecir(x)
        factores = sorted(
            (Factor(NOMBRES[k], round(v, 3)) for k, v in r.aportes.items() if v > 0),
            key=lambda f: -f.aporte,
        )[:3]
        nivel = nivel_de(r.probabilidad)
        return EvaluacionRiesgoModelo(
            **base,
            nivel=nivel,
            probabilidad=round(r.probabilidad, 4),
            factores=factores,
            basada_en_hasta=ultima.medido_en,
            mensaje=(
                f"Probabilidad de evento crítico en {HORIZONTE_HORAS} h: "
                f"{r.probabilidad:.0%} ({nivel.value})"
            ),
        )
