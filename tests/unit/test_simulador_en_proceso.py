"""Sensor simulado dentro de la app (Issue #23): ciclo de vida de las simulaciones."""

import threading

import pytest

from src.adapters.inbound.simulator.en_proceso import (
    MAXIMO_SIMULACIONES,
    ErrorSimulacion,
    SimuladorEnProceso,
)


class PasoFalso:
    def __init__(self, fallar_en: int | None = None):
        self.llamadas = []
        self.hubo_llamada = threading.Event()
        self._fallar_en = fallar_en

    def __call__(self, estanque_id, usuario_id, medicion):
        self.llamadas.append((estanque_id, usuario_id, medicion))
        self.hubo_llamada.set()
        if self._fallar_en is not None and len(self.llamadas) >= self._fallar_en:
            raise RuntimeError("estanque dado de baja")


def test_inicia_envia_la_primera_lectura_y_se_detiene():
    paso = PasoFalso()
    sim = SimuladorEnProceso(paso)
    estado = sim.iniciar(5, "critico_oxigeno", 60, usuario_id=2)
    assert paso.hubo_llamada.wait(3)
    assert estado.activa and sim.de(5) is estado and [s.estanque_id for s in sim.activas()] == [5]
    estanque, usuario, medicion = paso.llamadas[0]
    assert (estanque, usuario, medicion.oxigeno_mg_l) == (5, 2, 8.0)
    assert sim.detener(5) is True
    assert not estado.activa and sim.de(5) is None and sim.activas() == []
    assert sim.detener(5) is False
    assert estado.lecturas_enviadas == 1


def test_reiniciar_reemplaza_la_simulacion_del_mismo_estanque():
    sim = SimuladorEnProceso(PasoFalso())
    primera = sim.iniciar(1, "normal", 60, 1)
    segunda = sim.iniciar(1, "critico_temperatura", 60, 1)
    assert not primera.activa and segunda.activa and len(sim.activas()) == 1
    sim.detener_todas()
    assert sim.activas() == []


def test_un_error_detiene_la_simulacion_y_queda_registrado():
    paso = PasoFalso(fallar_en=1)
    sim = SimuladorEnProceso(paso)
    estado = sim.iniciar(3, "normal", 60, 1)
    assert paso.hubo_llamada.wait(3)
    estado._hilo.join(3)
    assert not estado.activa and estado.ultimo_error == "estanque dado de baja"
    assert sim.de(3) is None


@pytest.mark.parametrize(
    ("escenario", "intervalo", "mensaje"),
    [("tsunami", 5, "Escenario"), ("normal", 0.5, "intervalo"), ("normal", 61, "intervalo")],
)
def test_parametros_invalidos(escenario, intervalo, mensaje):
    with pytest.raises(ErrorSimulacion, match=mensaje):
        SimuladorEnProceso(PasoFalso()).iniciar(1, escenario, intervalo, 1)


def test_limite_de_simulaciones_simultaneas():
    sim = SimuladorEnProceso(PasoFalso())
    for i in range(MAXIMO_SIMULACIONES):
        sim.iniciar(i, "normal", 60, 1)
    with pytest.raises(ErrorSimulacion, match="Máximo"):
        sim.iniciar(99, "normal", 60, 1)
    sim.detener_todas()
