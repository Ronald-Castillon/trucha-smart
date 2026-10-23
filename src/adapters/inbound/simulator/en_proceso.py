"""Sensor simulado que corre dentro de la aplicación (ADR-004), controlado desde la web.

Cada simulación es un hilo que genera mediciones del escenario elegido y las entrega a
`ejecutar_paso`, que las registra por el mismo puerto de entrada `registrar_lectura` que usan
la API y el simulador de línea de comandos.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.adapters.inbound.simulator.escenarios import ESCENARIOS, Medicion, generar

INTERVALO_MINIMO_S = 1.0
INTERVALO_MAXIMO_S = 60.0
MAXIMO_SIMULACIONES = 10

# (estanque_id, usuario_id, medición) -> None. Lanza una excepción si la lectura no se registra.
EjecutarPaso = Callable[[int, int, Medicion], None]


class ErrorSimulacion(ValueError):
    """Parámetros de simulación inválidos o límite alcanzado."""


@dataclass
class EstadoSimulacion:
    estanque_id: int
    escenario: str
    intervalo_s: float
    usuario_id: int
    iniciada_en: datetime
    lecturas_enviadas: int = 0
    ultimo_error: str | None = None
    _detener: threading.Event = field(default_factory=threading.Event, repr=False)
    _hilo: threading.Thread | None = field(default=None, repr=False)

    @property
    def activa(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive() and not self._detener.is_set()


class SimuladorEnProceso:
    def __init__(self, ejecutar_paso: EjecutarPaso) -> None:
        self._ejecutar_paso = ejecutar_paso
        self._simulaciones: dict[int, EstadoSimulacion] = {}
        self._candado = threading.Lock()

    def iniciar(
        self, estanque_id: int, escenario: str, intervalo_s: float, usuario_id: int
    ) -> EstadoSimulacion:
        if escenario not in ESCENARIOS:
            raise ErrorSimulacion(f"Escenario desconocido. Opciones: {', '.join(ESCENARIOS)}")
        if not INTERVALO_MINIMO_S <= intervalo_s <= INTERVALO_MAXIMO_S:
            raise ErrorSimulacion(
                f"El intervalo debe estar entre {INTERVALO_MINIMO_S:g} y {INTERVALO_MAXIMO_S:g} s"
            )
        with self._candado:
            self._detener_sin_candado(estanque_id)
            if len(self.activas()) >= MAXIMO_SIMULACIONES:
                raise ErrorSimulacion(f"Máximo {MAXIMO_SIMULACIONES} simulaciones a la vez")
            estado = EstadoSimulacion(
                estanque_id, escenario, intervalo_s, usuario_id, datetime.now(UTC)
            )
            estado._hilo = threading.Thread(
                target=self._bucle, args=(estado,), daemon=True, name=f"sim-estanque-{estanque_id}"
            )
            self._simulaciones[estanque_id] = estado
            estado._hilo.start()
            return estado

    def detener(self, estanque_id: int) -> bool:
        with self._candado:
            return self._detener_sin_candado(estanque_id)

    def detener_todas(self) -> None:
        with self._candado:
            for estanque_id in list(self._simulaciones):
                self._detener_sin_candado(estanque_id)

    def activas(self) -> list[EstadoSimulacion]:
        return [s for s in self._simulaciones.values() if s.activa]

    def de(self, estanque_id: int) -> EstadoSimulacion | None:
        estado = self._simulaciones.get(estanque_id)
        return estado if estado is not None and estado.activa else None

    def _detener_sin_candado(self, estanque_id: int) -> bool:
        estado = self._simulaciones.pop(estanque_id, None)
        if estado is None:
            return False
        estado._detener.set()
        if estado._hilo is not None and estado._hilo is not threading.current_thread():
            estado._hilo.join(timeout=5)
        return True

    def _bucle(self, estado: EstadoSimulacion) -> None:
        for medicion in generar(estado.escenario):
            if estado._detener.is_set():
                return
            try:
                self._ejecutar_paso(estado.estanque_id, estado.usuario_id, medicion)
                estado.lecturas_enviadas += 1
                estado.ultimo_error = None
            except Exception as e:  # noqa: BLE001 - se informa y se detiene la simulación
                estado.ultimo_error = str(getattr(e, "mensaje", e))
                estado._detener.set()
                return
            if estado._detener.wait(estado.intervalo_s):
                return
