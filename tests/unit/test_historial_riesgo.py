"""RF-05: historial por fechas, estadísticas e índice de riesgo (dominio)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from src.domain.errores import ErrorValidacion, NoEncontrado
from src.domain.model.alerta import Alerta
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua, Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.indice_riesgo import Semaforo, calcular_indice_riesgo, semaforo_de
from src.domain.service.servicio_historial import ServicioHistorial
from tests.fakes import (
    RelojFijo,
    RepositorioAlertaMemoria,
    RepositorioEstanqueMemoria,
    RepositorioLecturaMemoria,
)
from tests.umbrales import UMBRALES

N, P, C = Nivel.NORMAL, Nivel.PRECAUCION, Nivel.CRITICA
T, OD, PH = Parametro.TEMPERATURA, Parametro.OXIGENO_DISUELTO, Parametro.PH
OPERARIO = Usuario("op", "Op", "h", Rol.OPERARIO, RelojFijo().ahora(), id=3)


@pytest.mark.parametrize(
    ("niveles", "alertas", "valor", "semaforo"),
    [
        ({T: N, OD: N, PH: N}, 0, 0, Semaforo.VERDE),
        ({T: P, OD: N, PH: N}, 0, 15, Semaforo.VERDE),
        ({T: P, OD: N, PH: N}, 1, 25, Semaforo.VERDE),
        ({T: P, OD: P, PH: N}, 0, 30, Semaforo.AMARILLO),
        ({T: N, OD: C, PH: N}, 0, 40, Semaforo.AMARILLO),
        ({T: N, OD: C, PH: N}, 1, 50, Semaforo.AMARILLO),
        ({T: P, OD: C, PH: N}, 0, 55, Semaforo.AMARILLO),
        ({T: N, OD: C, PH: N}, 2, 60, Semaforo.ROJO),
        ({T: C, OD: C, PH: N}, 0, 80, Semaforo.ROJO),
        ({T: C, OD: C, PH: C}, 3, 100, Semaforo.ROJO),
        ({}, 0, 0, Semaforo.VERDE),
        ({}, 3, 30, Semaforo.AMARILLO),
    ],
)
def test_cp_rf05_02_indice_de_riesgo_y_semaforo(niveles, alertas, valor, semaforo):
    """CP-RF05-02: riesgo = min(100, 40·críticos + 15·precaución + 10·alertas críticas)."""
    r = calcular_indice_riesgo(niveles, alertas)
    assert (r.valor, r.semaforo) == (valor, semaforo)
    assert r.formula.endswith(f"= {valor}")


@pytest.mark.parametrize(
    ("valor", "semaforo"),
    [
        (0, Semaforo.VERDE),
        (29, Semaforo.VERDE),
        (30, Semaforo.AMARILLO),
        (59, Semaforo.AMARILLO),
        (60, Semaforo.ROJO),
        (100, Semaforo.ROJO),
    ],
)
def test_limites_del_semaforo(valor, semaforo):
    assert semaforo_de(valor) is semaforo


def test_riesgo_rechaza_alertas_negativas():
    with pytest.raises(ValueError):
        calcular_indice_riesgo({}, -1)


def test_etiquetas_y_formula():
    r = calcular_indice_riesgo({T: C, OD: P}, 1)
    assert r.nivel == "alto" and r.formula == "min(100, 40×1 + 15×1 + 10×1) = min(100, 65) = 65"


# --------------------------------------------------------------------------- servicio


@pytest.fixture
def entorno():
    reloj = RelojFijo(datetime(2026, 10, 23, 12, 0, tzinfo=UTC))
    estanques = RepositorioEstanqueMemoria()
    eid = estanques.guardar(Estanque("A1", TipoEstanque.ESTANQUE, reloj.ahora())).id
    lecturas = RepositorioLecturaMemoria()
    alertas = RepositorioAlertaMemoria()
    for dia in range(10, 23):  # 13 días, 2 lecturas por día
        for hora, od in ((6, 8.0), (18, 6.0)):
            lecturas.guardar(
                LecturaAgua(
                    eid,
                    12.0 + dia / 100,
                    od,
                    7.2,
                    FuenteLectura.SENSOR,
                    datetime(2026, 10, dia, hora, tzinfo=UTC),
                )
            )
    srv = ServicioHistorial(lecturas, estanques, alertas, EvaluadorCalidadAgua(UMBRALES), reloj)
    return srv, lecturas, alertas, eid, reloj


def test_cp_rf05_01_filtra_por_rango_de_fechas(entorno):
    """CP-RF05-01: solo las lecturas del rango, en orden cronológico, con niveles y estadísticas."""
    srv, *_, eid, _ = entorno
    h = srv.historial(eid, OPERARIO, date(2026, 10, 16), date(2026, 10, 18))
    assert len(h.lecturas) == 6
    fechas = [x.lectura.medido_en for x in h.lecturas]
    assert fechas == sorted(fechas)
    assert fechas[0] == datetime(2026, 10, 16, 6, tzinfo=UTC)
    assert fechas[-1] == datetime(2026, 10, 18, 18, tzinfo=UTC)
    assert [x.niveles[OD] for x in h.lecturas[:2]] == [N, P]
    od = h.estadisticas[OD]
    assert (od.minimo, od.maximo, od.promedio) == (6.0, 8.0, 7.0)


def test_historial_por_defecto_ultimos_7_dias(entorno):
    srv, *_, eid, _ = entorno
    h = srv.historial(eid, OPERARIO)
    assert (h.desde, h.hasta) == (date(2026, 10, 17), date(2026, 10, 23))
    assert len(h.lecturas) == 12  # 17..22 con 2 lecturas por día


def test_historial_vacio_y_validaciones(entorno):
    srv, *_, eid, _ = entorno
    vacio = srv.historial(eid, OPERARIO, date(2026, 1, 1), date(2026, 1, 2))
    assert vacio.lecturas == [] and vacio.estadisticas == {}
    with pytest.raises(ErrorValidacion, match="posterior"):
        srv.historial(eid, OPERARIO, date(2026, 10, 20), date(2026, 10, 19))
    with pytest.raises(ErrorValidacion, match="366"):
        srv.historial(eid, OPERARIO, date(2025, 1, 1), date(2026, 10, 1))
    with pytest.raises(NoEncontrado):
        srv.historial(99, OPERARIO)
    with pytest.raises(NoEncontrado):
        srv.riesgo(99, OPERARIO)


def test_cp_rf05_02_riesgo_usa_ultima_lectura_y_alertas_criticas(entorno):
    """CP-RF05-02: última lectura con OD en precaución (15) + 2 alertas críticas abiertas (20)."""
    srv, lecturas, alertas, eid, reloj = entorno
    assert srv.riesgo(eid, OPERARIO).valor == 15
    for n in range(2):
        alertas.guardar(Alerta(eid, 1, OD, C, 4.0, "x", reloj.ahora() + timedelta(minutes=n)))
    alertas.guardar(Alerta(eid, 1, T, P, 17.0, "x", reloj.ahora()))  # precaución: no suma
    r = srv.riesgo(eid, OPERARIO)
    assert (r.valor, r.semaforo, r.alertas_criticas_abiertas) == (35, Semaforo.AMARILLO, 2)
