"""Caso de uso predecir_tendencia: proyección de cada parámetro del estanque (RF-10)."""

from __future__ import annotations

from datetime import timedelta

from src.domain.errores import NoEncontrado
from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import ConjuntoUmbrales
from src.domain.model.usuario import Permiso, Usuario
from src.domain.service.predictor_tendencia import EstadoPrediccion, predecir
from src.ports.inbound.predecir_tendencia import PrediccionEstanque
from src.ports.outbound.repositorio_estanque import RepositorioEstanque
from src.ports.outbound.repositorio_lectura import RepositorioLectura

VENTANA = timedelta(hours=24)
ORDEN = {
    EstadoPrediccion.YA_CRITICO: 0,
    EstadoPrediccion.RIESGO: 1,
    EstadoPrediccion.SIN_RIESGO: 2,
    EstadoPrediccion.DATOS_INSUFICIENTES: 3,
}


class ServicioPrediccion:
    """Implementa el puerto de entrada PredecirTendencia."""

    def __init__(
        self,
        lecturas: RepositorioLectura,
        estanques: RepositorioEstanque,
        umbrales: ConjuntoUmbrales,
    ) -> None:
        self._lecturas = lecturas
        self._estanques = estanques
        self._umbrales = umbrales

    def predecir(self, estanque_id: int, solicitante: Usuario) -> PrediccionEstanque:
        solicitante.exigir(Permiso.CONSULTAR)
        estanque = self._estanques.por_id(estanque_id)
        if estanque is None:
            raise NoEncontrado(f"No existe el estanque {estanque_id}")
        ultima = self._lecturas.ultima_de(estanque_id)
        lecturas = (
            self._lecturas.de_estanque(estanque_id, ultima.medido_en - VENTANA, ultima.medido_en)
            if ultima
            else []
        )
        predicciones = [
            predecir(p, [(x.medido_en, x.valores()[p]) for x in lecturas], self._umbrales.de(p))
            for p in Parametro
        ]
        principal = min(
            predicciones,
            key=lambda pr: (ORDEN[pr.estado], pr.horas_hasta_limite or 0.0),
        )
        return PrediccionEstanque(
            estanque, ultima.medido_en if ultima else None, predicciones, principal
        )
