"""RF-03: lecturas de calidad de agua (dominio)."""

import math
from datetime import UTC, datetime, timedelta

import pytest

from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado, PermisoDenegado
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua, Parametro
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.servicio_lecturas import ServicioLecturas
from src.ports.inbound.registrar_lectura import ComandoRegistrarLectura
from tests.fakes import RelojFijo, RepositorioEstanqueMemoria, RepositorioLecturaMemoria

OPERARIO = Usuario("op", "Op", "h", Rol.OPERARIO, RelojFijo().ahora(), id=7)


def _lectura(t=12.0, od=8.0, ph=7.2) -> LecturaAgua:
    return LecturaAgua(1, t, od, ph, FuenteLectura.MANUAL, RelojFijo().ahora())


@pytest.mark.parametrize(
    ("t", "od", "ph"),
    [(0, 0, 0), (40, 0, 14), (12.5, 25.0, 7.0)],
)
def test_lecturas_en_limites_fisicos_son_validas(t, od, ph):
    assert _lectura(t, od, ph).valores()[Parametro.PH] == ph


@pytest.mark.parametrize(
    ("t", "od", "ph", "campo"),
    [
        (-0.1, 8, 7, "temperatura_c"),
        (40.1, 8, 7, "temperatura_c"),
        (12, -0.01, 7, "oxigeno_mg_l"),
        (12, 8, -0.5, "ph"),
        (12, 8, 14.01, "ph"),
        (12, 8, math.nan, "ph"),
        (12, None, 7, "oxigeno_mg_l"),
    ],
)
def test_cp_rf03_02_valores_fisicamente_imposibles(t, od, ph, campo):
    """CP-RF03-02: pH fuera de 0-14, OD < 0 o temperatura fuera de 0-40 se rechazan."""
    with pytest.raises(ErrorValidacion) as e:
        _lectura(t, od, ph)
    assert e.value.campo == campo


def test_mensaje_de_valor_imposible_es_claro():
    with pytest.raises(
        ErrorValidacion, match=r"El pH 15 es físicamente imposible \(debe estar entre 0 y 14\)"
    ):
        _lectura(ph=15)
    with pytest.raises(ErrorValidacion, match=r"debe estar >= 0"):
        _lectura(od=-1)


@pytest.fixture
def entorno():
    reloj = RelojFijo()
    estanques = RepositorioEstanqueMemoria()
    activo = estanques.guardar(Estanque("A1", TipoEstanque.ESTANQUE, reloj.ahora()))
    baja = estanques.guardar(Estanque("B", TipoEstanque.JAULA, reloj.ahora(), activo=False))
    srv = ServicioLecturas(RepositorioLecturaMemoria(), estanques, reloj)
    return srv, reloj, activo.id, baja.id


def _cmd(estanque_id, **kw):
    datos = {"temperatura_c": 12.4, "oxigeno_mg_l": 8.2, "ph": 7.3} | kw
    return ComandoRegistrarLectura(estanque_id=estanque_id, **datos)


def test_cp_rf03_01_lectura_valida_queda_como_ultima(entorno):
    """CP-RF03-01: la lectura se guarda con usuario y fecha/hora y es la última del estanque."""
    srv, reloj, eid, _ = entorno
    srv.registrar(_cmd(eid), OPERARIO)
    reloj.avanzar(minutes=5)
    lec = srv.registrar(_cmd(eid, oxigeno_mg_l=7.9, fuente=FuenteLectura.SENSOR), OPERARIO)
    assert lec.registrado_por == 7 and lec.medido_en == reloj.ahora()
    assert srv.ultima(eid, OPERARIO) == lec
    assert [x.oxigeno_mg_l for x in srv.recientes(eid, OPERARIO)] == [7.9, 8.2]
    assert len(srv.recientes(eid, OPERARIO, limite=0)) == 1


def test_cp_rf03_02_lectura_imposible_no_se_guarda(entorno):
    """CP-RF03-02: el servicio rechaza la lectura y no guarda nada."""
    srv, _, eid, _ = entorno
    with pytest.raises(ErrorValidacion):
        srv.registrar(_cmd(eid, ph=15), OPERARIO)
    assert srv.ultima(eid, OPERARIO) is None


def test_fecha_de_medicion_explicita(entorno):
    srv, reloj, eid, _ = entorno
    antes = reloj.ahora() - timedelta(hours=1)
    assert srv.registrar(_cmd(eid, medido_en=antes), OPERARIO).medido_en == antes
    with pytest.raises(ErrorValidacion, match="futura"):
        srv.registrar(_cmd(eid, medido_en=reloj.ahora() + timedelta(minutes=10)), OPERARIO)
    with pytest.raises(ErrorValidacion, match="zona horaria"):
        srv.registrar(_cmd(eid, medido_en=datetime(2026, 10, 23, 10, 0)), OPERARIO)
    tolerada = reloj.ahora() + timedelta(minutes=4)
    assert srv.registrar(_cmd(eid, medido_en=tolerada), OPERARIO).medido_en.tzinfo == UTC


def test_estanque_inexistente_o_de_baja(entorno):
    srv, _, _, baja = entorno
    with pytest.raises(NoEncontrado):
        srv.registrar(_cmd(99), OPERARIO)
    with pytest.raises(NoEncontrado):
        srv.ultima(99, OPERARIO)
    with pytest.raises(Conflicto):
        srv.registrar(_cmd(baja), OPERARIO)


def test_usuario_inactivo_no_registra(entorno):
    srv, _, eid, _ = entorno
    inactivo = Usuario("x", "X", "h", Rol.ADMINISTRADOR, RelojFijo().ahora(), activo=False, id=3)
    with pytest.raises(PermisoDenegado):
        srv.registrar(_cmd(eid), inactivo)
