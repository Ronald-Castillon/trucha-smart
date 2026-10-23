"""RF-04: umbrales, evaluación de calidad de agua y alertas (dominio)."""

from datetime import timedelta

import pytest

from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado, PermisoDenegado
from src.domain.model.alerta import Alerta, EstadoAlerta
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua, Parametro
from src.domain.model.umbral import ConjuntoUmbrales, Nivel, Umbral
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.servicio_alertas import ServicioAlertas
from src.domain.service.servicio_lecturas import ServicioLecturas
from src.ports.inbound.registrar_lectura import ComandoRegistrarLectura
from tests.fakes import (
    NotificadorFalso,
    RelojFijo,
    RepositorioAlertaMemoria,
    RepositorioEstanqueMemoria,
    RepositorioLecturaMemoria,
)
from tests.umbrales import UMBRALES

OPERARIO = Usuario("op", "Op", "h", Rol.OPERARIO, RelojFijo().ahora(), id=3)

# --------------------------------------------------------------------------- valores límite


@pytest.mark.parametrize(
    ("valor", "nivel"),
    [
        (7.99, Nivel.CRITICA),
        (8.0, Nivel.PRECAUCION),
        (9.99, Nivel.PRECAUCION),
        (10.0, Nivel.NORMAL),
        (13.0, Nivel.NORMAL),
        (16.0, Nivel.NORMAL),
        (16.01, Nivel.PRECAUCION),
        (18.0, Nivel.PRECAUCION),
        (18.01, Nivel.CRITICA),
    ],
)
def test_limites_temperatura(valor, nivel):
    assert UMBRALES.temperatura.clasificar(valor) is nivel


@pytest.mark.parametrize(
    ("valor", "nivel"),
    [
        (4.99, Nivel.CRITICA),
        (5.0, Nivel.PRECAUCION),
        (6.99, Nivel.PRECAUCION),
        (7.0, Nivel.NORMAL),
        (12.0, Nivel.NORMAL),
        (0.0, Nivel.CRITICA),
    ],
)
def test_limites_oxigeno_disuelto(valor, nivel):
    assert UMBRALES.oxigeno_disuelto.clasificar(valor) is nivel


@pytest.mark.parametrize(
    ("valor", "nivel"),
    [
        (5.99, Nivel.CRITICA),
        (6.0, Nivel.PRECAUCION),
        (6.49, Nivel.PRECAUCION),
        (6.5, Nivel.NORMAL),
        (8.5, Nivel.NORMAL),
        (8.51, Nivel.PRECAUCION),
        (9.0, Nivel.PRECAUCION),
        (9.01, Nivel.CRITICA),
    ],
)
def test_limites_ph(valor, nivel):
    assert UMBRALES.ph.clasificar(valor) is nivel


def test_umbral_invalido_se_rechaza():
    with pytest.raises(ErrorValidacion, match="debe contener"):
        Umbral(Parametro.PH, "pH", 6.0, 9.0, 6.5, 8.5)
    with pytest.raises(ErrorValidacion, match="debe contener"):
        Umbral(Parametro.OXIGENO_DISUELTO, "mg/L", None, None, 5.0, None)
    with pytest.raises(ErrorValidacion, match="mínimo mayor"):
        Umbral(Parametro.PH, "pH", 9.0, 6.0, None, None)
    with pytest.raises(ErrorValidacion, match="mal asignado"):
        ConjuntoUmbrales(UMBRALES.ph, UMBRALES.oxigeno_disuelto, UMBRALES.ph)


def test_mensajes_de_umbral():
    u = UMBRALES
    assert u.oxigeno_disuelto.describir(4.5, Nivel.CRITICA) == (
        "Oxígeno disuelto en CRÍTICA: 4.50 mg/L (normal >= 7 mg/L)"
    )
    assert u.ph.describir(9.2, Nivel.CRITICA) == "pH en CRÍTICA: 9.20 (normal 6.5–8.5)"
    sin_limites = Umbral(Parametro.PH, "", None, 8.0, None, None)
    assert sin_limites.rango_normal == "<= 8"
    assert Umbral(Parametro.PH, "", None, None, None, None).rango_normal == "cualquier valor"


def test_evaluador_devuelve_un_nivel_por_parametro():
    lectura = LecturaAgua(1, 17.0, 4.5, 7.0, FuenteLectura.SENSOR, RelojFijo().ahora())
    niveles = EvaluadorCalidadAgua(UMBRALES).niveles(lectura)
    assert niveles == {
        Parametro.TEMPERATURA: Nivel.PRECAUCION,
        Parametro.OXIGENO_DISUELTO: Nivel.CRITICA,
        Parametro.PH: Nivel.NORMAL,
    }


# --------------------------------------------------------------------------- alertas


@pytest.fixture
def entorno():
    reloj = RelojFijo()
    estanques = RepositorioEstanqueMemoria()
    eid = estanques.guardar(Estanque("A1", TipoEstanque.ESTANQUE, reloj.ahora())).id
    alertas = RepositorioAlertaMemoria()
    notificador = NotificadorFalso()
    lecturas = ServicioLecturas(
        RepositorioLecturaMemoria(),
        estanques,
        alertas,
        EvaluadorCalidadAgua(UMBRALES),
        notificador,
        reloj,
    )
    return lecturas, ServicioAlertas(alertas, reloj), notificador, reloj, eid


def _registrar(srv, eid, t=12.0, od=8.0, ph=7.2):
    return srv.registrar(ComandoRegistrarLectura(eid, t, od, ph), OPERARIO)


@pytest.mark.parametrize(
    ("od", "nivel"),
    [(4.5, Nivel.CRITICA), (6.0, Nivel.PRECAUCION), (7.0, None)],
)
def test_cp_rf04_01_alerta_segun_umbral_de_oxigeno(entorno, od, nivel):
    """CP-RF04-01: OD 4.5 -> CRÍTICA, OD 6 -> PRECAUCIÓN, OD 7 -> sin alerta."""
    lecturas, _, notificador, _, eid = entorno
    resultado = _registrar(lecturas, eid, od=od)
    if nivel is None:
        assert resultado.alertas_nuevas == [] and notificador.enviadas == []
        return
    (alerta,) = resultado.alertas_nuevas
    assert alerta.parametro is Parametro.OXIGENO_DISUELTO and alerta.nivel is nivel
    assert alerta.estado is EstadoAlerta.ABIERTA and alerta.lectura_id == resultado.lectura.id
    assert notificador.enviadas == [alerta]
    assert lecturas.estado(eid, OPERARIO).alertas_abiertas == [alerta]


def test_varios_parametros_fuera_de_rango_generan_varias_alertas(entorno):
    lecturas, *_, eid = entorno
    resultado = _registrar(lecturas, eid, t=19, od=4.0, ph=9.5)
    assert {(a.parametro, a.nivel) for a in resultado.alertas_nuevas} == {
        (Parametro.TEMPERATURA, Nivel.CRITICA),
        (Parametro.OXIGENO_DISUELTO, Nivel.CRITICA),
        (Parametro.PH, Nivel.CRITICA),
    }


def test_cp_rf04_02_no_duplica_y_atender_registra_usuario_y_fecha(entorno):
    """CP-RF04-02: no se duplica una alerta abierta; atender registra usuario y fecha/hora."""
    lecturas, alertas, _, reloj, eid = entorno
    primera = _registrar(lecturas, eid, od=4.5).alertas_nuevas[0]
    reloj.avanzar(minutes=5)
    assert _registrar(lecturas, eid, od=4.2).alertas_nuevas == []
    # Cambiar de nivel sí crea otra alerta (otro nivel).
    assert len(_registrar(lecturas, eid, od=6.0).alertas_nuevas) == 1
    assert len(alertas.listar(OPERARIO, eid, EstadoAlerta.ABIERTA)) == 2

    reloj.avanzar(minutes=3)
    atendida = alertas.atender(primera.id, "  Aireador encendido ", OPERARIO)
    assert atendida.estado is EstadoAlerta.ATENDIDA
    assert atendida.atendida_por == OPERARIO.id and atendida.atendida_en == reloj.ahora()
    assert atendida.observacion == "Aireador encendido"
    # Tras atenderla, una nueva condición crítica vuelve a alertar.
    assert len(_registrar(lecturas, eid, od=4.0).alertas_nuevas) == 1


def test_atender_alerta_ya_atendida_o_inexistente(entorno):
    lecturas, alertas, *_, eid = entorno
    alerta = _registrar(lecturas, eid, od=4.5).alertas_nuevas[0]
    alertas.atender(alerta.id, None, OPERARIO)
    with pytest.raises(Conflicto):
        alertas.atender(alerta.id, None, OPERARIO)
    with pytest.raises(NoEncontrado):
        alertas.atender(999, None, OPERARIO)


def test_atender_requiere_permiso(entorno):
    lecturas, alertas, *_, eid = entorno
    alerta = _registrar(lecturas, eid, od=4.5).alertas_nuevas[0]
    inactivo = Usuario("x", "X", "h", Rol.OPERARIO, RelojFijo().ahora(), activo=False, id=9)
    with pytest.raises(PermisoDenegado):
        alertas.atender(alerta.id, None, inactivo)


def test_alerta_valida_nivel_y_observacion():
    ahora = RelojFijo().ahora()
    with pytest.raises(ErrorValidacion):
        Alerta(1, 1, Parametro.PH, Nivel.NORMAL, 7.0, "x", ahora)
    alerta = Alerta(1, 1, Parametro.PH, Nivel.CRITICA, 9.5, "x", ahora, id=1)
    with pytest.raises(ErrorValidacion):
        alerta.atender(1, ahora + timedelta(minutes=1), "x" * 256)
    alerta.atender(1, ahora, "")
    assert alerta.observacion is None


def test_estado_sin_lecturas(entorno):
    lecturas, *_, eid = entorno
    estado = lecturas.estado(eid, OPERARIO)
    assert estado.lectura is None and estado.niveles == {} and estado.alertas_abiertas == []
