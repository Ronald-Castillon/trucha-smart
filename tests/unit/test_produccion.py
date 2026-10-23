"""RF-06: alimentación, mortalidad, biomasa y FCR (dominio)."""

import math
from datetime import date, timedelta

import pytest

from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado, PermisoDenegado
from src.domain.model.lote import Lote
from src.domain.model.registro_alimentacion import RegistroAlimentacion
from src.domain.model.registro_mortalidad import RegistroMortalidad
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.calculadora_fcr import (
    NO_CALCULABLE,
    biomasa_kg,
    calcular_fcr,
    peces_vivos,
    resumen_produccion,
)
from src.domain.service.servicio_produccion import ServicioProduccion
from tests.fakes import (
    RelojFijo,
    RepositorioAlimentacionMemoria,
    RepositorioLoteMemoria,
    RepositorioMortalidadMemoria,
)

OPERARIO = Usuario("op", "Op", "h", Rol.OPERARIO, RelojFijo().ahora(), id=3)
AHORA = RelojFijo().ahora()


def _lote(peces=1000, inicial=50.0, actual=80.0, activo=True) -> Lote:
    return Lote(1, "L-1", peces, inicial, actual, date(2026, 9, 1), activo=activo, id=1)


# --------------------------------------------------------------------------- cálculo


def test_biomasa_es_peces_vivos_por_peso_medio():
    assert biomasa_kg(990, 80.0) == 79.2
    assert peces_vivos(_lote(), 10) == 990


def test_cp_rf06_01_fcr_alimento_sobre_ganancia_de_biomasa():
    """CP-RF06-01: biomasa = vivos × peso; FCR = alimento total / ganancia."""
    # inicial 1000 × 50 g = 50 kg; actual 990 × 80 g = 79.2 kg; ganancia 29.2 kg
    r = resumen_produccion(_lote(), mortalidad_total=10, alimento_total_kg=35.04)
    assert (r.peces_vivos, r.biomasa_inicial_kg, r.biomasa_kg) == (990, 50.0, 79.2)
    assert r.ganancia_biomasa_kg == 29.2
    assert r.fcr == 1.2 and r.fcr_texto == "1.20"
    assert r.supervivencia_pct == 99.0
    assert "35.040 kg de alimento / 29.200 kg de ganancia = 1.20" in r.fcr_detalle


def test_cp_rf06_02_ganancia_cero_fcr_no_calculable():
    """CP-RF06-02: con ganancia 0 el FCR es "no calculable" sin error."""
    r = resumen_produccion(_lote(actual=50.0), mortalidad_total=0, alimento_total_kg=12.0)
    assert r.ganancia_biomasa_kg == 0
    assert r.fcr is None and r.fcr_texto == NO_CALCULABLE
    assert "ganancia de biomasa es 0" in r.fcr_detalle


def test_fcr_ganancia_negativa_no_calculable():
    r = resumen_produccion(_lote(actual=50.0), mortalidad_total=100, alimento_total_kg=5)
    assert r.ganancia_biomasa_kg == -5.0 and r.fcr is None
    assert "disminuyó 5.000 kg" in r.fcr_detalle


def test_fcr_sin_alimento_es_cero():
    assert calcular_fcr(0, 10)[0] == 0.0
    with pytest.raises(ErrorValidacion):
        calcular_fcr(-1, 10)


def test_mortalidad_acumulada_invalida():
    with pytest.raises(ErrorValidacion):
        peces_vivos(_lote(), -1)
    with pytest.raises(ErrorValidacion, match="supera los peces sembrados"):
        peces_vivos(_lote(), 1001)


@pytest.mark.parametrize("kg", [0, -2.5, math.nan, None, 10_001])
def test_alimentacion_invalida(kg):
    with pytest.raises(ErrorValidacion) as e:
        RegistroAlimentacion(1, kg, AHORA)
    assert e.value.campo == "cantidad_kg"


@pytest.mark.parametrize("n", [0, -1, 2.5, True])
def test_mortalidad_invalida(n):
    with pytest.raises(ErrorValidacion) as e:
        RegistroMortalidad(1, n, AHORA)
    assert e.value.campo == "cantidad"


def test_mortalidad_causa():
    assert RegistroMortalidad(1, 3, AHORA, causa="  ").causa is None
    with pytest.raises(ErrorValidacion):
        RegistroMortalidad(1, 3, AHORA, causa="x" * 121)


# --------------------------------------------------------------------------- servicio


@pytest.fixture
def srv():
    lotes = RepositorioLoteMemoria()
    lotes.guardar(_lote())
    lotes.guardar(Lote(1, "L-0", 10, 1, 1, date(2026, 1, 1), activo=False, id=2))
    lotes._siguiente = 3
    return ServicioProduccion(
        lotes, RepositorioAlimentacionMemoria(), RepositorioMortalidadMemoria(), RelojFijo()
    )


def test_cp_rf06_01_registros_actualizan_el_resumen(srv):
    """CP-RF06-01: la alimentación y la mortalidad registradas se reflejan en biomasa y FCR."""
    a = srv.registrar_alimentacion(1, 20.0, OPERARIO)
    srv.registrar_alimentacion(1, 15.04, OPERARIO, AHORA - timedelta(days=1))
    m = srv.registrar_mortalidad(1, 10, " Manipulación ", OPERARIO)
    assert a.registrado_por == OPERARIO.id and a.registrado_en == AHORA
    assert m.causa == "Manipulación"
    r = srv.produccion(1, OPERARIO)
    assert (r.alimento_total_kg, r.mortalidad_total, r.fcr) == (35.04, 10, 1.2)
    assert [x.cantidad_kg for x in srv.alimentaciones(1, OPERARIO)] == [20.0, 15.04]
    assert len(srv.mortalidades(1, OPERARIO)) == 1


def test_mortalidad_no_supera_peces_vivos(srv):
    srv.registrar_mortalidad(1, 990, None, OPERARIO)
    with pytest.raises(ErrorValidacion, match=r"supera los peces vivos del lote \(10\)"):
        srv.registrar_mortalidad(1, 11, None, OPERARIO)
    srv.registrar_mortalidad(1, 10, None, OPERARIO)
    assert srv.produccion(1, OPERARIO).peces_vivos == 0


def test_lote_cerrado_inexistente_y_fechas(srv):
    with pytest.raises(Conflicto):
        srv.registrar_alimentacion(2, 5, OPERARIO)
    with pytest.raises(NoEncontrado):
        srv.produccion(99, OPERARIO)
    with pytest.raises(ErrorValidacion, match="futura"):
        srv.registrar_alimentacion(1, 5, OPERARIO, AHORA + timedelta(hours=1))
    with pytest.raises(ErrorValidacion, match="zona horaria"):
        srv.registrar_mortalidad(1, 1, None, OPERARIO, AHORA.replace(tzinfo=None))


def test_permisos(srv):
    inactivo = Usuario("x", "X", "h", Rol.OPERARIO, AHORA, activo=False, id=9)
    with pytest.raises(PermisoDenegado):
        srv.registrar_alimentacion(1, 5, inactivo)
