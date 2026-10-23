"""Caso de uso consultar_historial: historial por fechas, estadísticas y riesgo (RF-05)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from src.domain.errores import ErrorValidacion, NoEncontrado
from src.domain.model.alerta import EstadoAlerta
from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Permiso, Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.indice_riesgo import IndiceRiesgo, calcular_indice_riesgo
from src.ports.inbound.consultar_historial import Estadistica, Historial, LecturaEvaluada
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_alerta import RepositorioAlerta
from src.ports.outbound.repositorio_estanque import RepositorioEstanque
from src.ports.outbound.repositorio_lectura import RepositorioLectura

DIAS_POR_DEFECTO = 7
MAXIMO_DIAS = 366


class ServicioHistorial:
    """Implementa el puerto de entrada ConsultarHistorial."""

    def __init__(
        self,
        lecturas: RepositorioLectura,
        estanques: RepositorioEstanque,
        alertas: RepositorioAlerta,
        evaluador: EvaluadorCalidadAgua,
        reloj: Reloj,
    ) -> None:
        self._lecturas = lecturas
        self._estanques = estanques
        self._alertas = alertas
        self._evaluador = evaluador
        self._reloj = reloj

    def historial(
        self,
        estanque_id: int,
        solicitante: Usuario,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> Historial:
        solicitante.exigir(Permiso.CONSULTAR)
        estanque = self._estanque(estanque_id)
        hasta = hasta or self._reloj.ahora().date()
        desde = desde or hasta - timedelta(days=DIAS_POR_DEFECTO - 1)
        if desde > hasta:
            raise ErrorValidacion("desde", "La fecha 'desde' no puede ser posterior a 'hasta'")
        if (hasta - desde).days + 1 > MAXIMO_DIAS:
            raise ErrorValidacion("desde", f"El rango máximo es de {MAXIMO_DIAS} días")
        inicio = datetime.combine(desde, time.min, tzinfo=UTC)
        fin = datetime.combine(hasta, time.max, tzinfo=UTC)
        lecturas = sorted(
            self._lecturas.de_estanque(estanque_id, inicio, fin),
            key=lambda x: (x.medido_en, x.id or 0),
        )
        evaluadas = [LecturaEvaluada(x, self._evaluador.niveles(x)) for x in lecturas]
        estadisticas = {}
        for parametro in Parametro:
            valores = [x.valores()[parametro] for x in lecturas]
            if valores:
                estadisticas[parametro] = Estadistica(
                    minimo=min(valores),
                    maximo=max(valores),
                    promedio=round(sum(valores) / len(valores), 2),
                )
        return Historial(estanque, desde, hasta, evaluadas, estadisticas)

    def riesgo(self, estanque_id: int, solicitante: Usuario) -> IndiceRiesgo:
        solicitante.exigir(Permiso.CONSULTAR)
        self._estanque(estanque_id)
        ultima = self._lecturas.ultima_de(estanque_id)
        niveles = self._evaluador.niveles(ultima) if ultima else {}
        criticas = [
            a
            for a in self._alertas.listar(estanque_id, EstadoAlerta.ABIERTA)
            if a.nivel is Nivel.CRITICA
        ]
        return calcular_indice_riesgo(niveles, len(criticas))

    def _estanque(self, estanque_id: int):
        estanque = self._estanques.por_id(estanque_id)
        if estanque is None:
            raise NoEncontrado(f"No existe el estanque {estanque_id}")
        return estanque
