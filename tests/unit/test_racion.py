"""RF-07: recomendación de ración diaria (dominio)."""

from datetime import date

import pytest

from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua
from src.domain.model.lote import Lote
from src.domain.model.registro_mortalidad import RegistroMortalidad
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.recomendador_racion import (
    RecomendadorRacion,
    TablaAlimentacion,
    TramoTasa,
)
from src.domain.service.servicio_racion import ServicioRacion
from tests.fakes import (
    RelojFijo,
    RepositorioLecturaMemoria,
    RepositorioLoteMemoria,
    RepositorioMortalidadMemoria,
)
from tests.umbrales import UMBRALES

N, P, C = Nivel.NORMAL, Nivel.PRECAUCION, Nivel.CRITICA
FACTOR_T = {N: 1.0, P: 0.7, C: 0.0}
FACTOR_O = {N: 1.0, P: 0.5, C: 0.0}
TABLA = TablaAlimentacion(
    tramos=(
        TramoTasa(0, 10, 5.0),
        TramoTasa(10, 50, 3.0),
        TramoTasa(50, 200, 2.0),
        TramoTasa(200, None, 1.2),
    ),
    factor_temperatura=FACTOR_T,
    factor_oxigeno=FACTOR_O,
)
REC = RecomendadorRacion(TABLA)
OPERARIO = Usuario("op", "Op", "h", Rol.OPERARIO, RelojFijo().ahora(), id=3)


@pytest.mark.parametrize(
    ("peso", "tasa"),
    [
        (0.5, 5.0),
        (9.99, 5.0),
        (10, 3.0),
        (49.99, 3.0),
        (50, 2.0),
        (199.99, 2.0),
        (200, 1.2),
        (1500, 1.2),
    ],
)
def test_tasa_segun_peso_medio_en_los_limites(peso, tasa):
    assert REC.recomendar(100, peso, N, N).tasa_pct == tasa


def test_cp_rf07_01_racion_con_agua_normal_y_regla_visible():
    """CP-RF07-01: ración = biomasa × tasa × factor T × factor O, mostrando la regla."""
    r = REC.recomendar(biomasa_kg=310.0, peso_medio_g=62.0, nivel_temperatura=N, nivel_oxigeno=N)
    assert r.racion_kg == 6.2 and not r.suspender  # 310 × 2 %
    assert r.regla == (
        "Ración = 310.000 kg de biomasa × 2 % (peso medio 62 g, tramo 50–200 g) "
        "× 1 (temperatura normal) × 1 (oxígeno normal) = 6.200 kg/día"
    )


@pytest.mark.parametrize(
    ("n_t", "n_o", "racion"),
    [(P, N, 4.34), (N, P, 3.1), (P, P, 2.17)],  # 6.2 × 0.7, × 0.5, × 0.35
)
def test_factores_de_precaucion(n_t, n_o, racion):
    r = REC.recomendar(310.0, 62.0, n_t, n_o)
    assert r.racion_kg == racion and not r.suspender


@pytest.mark.parametrize(
    ("n_t", "n_o", "motivo"),
    [
        (C, N, "temperatura"),
        (N, C, "oxígeno disuelto"),
        (C, C, "temperatura y oxígeno disuelto"),
        (P, C, "oxígeno disuelto"),
    ],
)
def test_cp_rf07_02_nivel_critico_suspende_alimentacion(n_t, n_o, motivo):
    """CP-RF07-02: con temperatura u oxígeno CRÍTICO la ración es 0 y se indica suspender."""
    r = REC.recomendar(310.0, 62.0, n_t, n_o)
    assert r.racion_kg == 0 and r.suspender
    assert r.regla.startswith(f"Suspender alimentación: {motivo} en nivel CRÍTICO.")


def test_sin_lectura_asume_normal_con_advertencia():
    r = REC.recomendar(100, 30, None, None)
    assert r.racion_kg == 3.0 and r.advertencias and "Sin lectura" in r.advertencias[0]


def test_tramos_descripcion():
    assert [t.descripcion for t in TABLA.tramos] == ["< 10 g", "10–50 g", "50–200 g", ">= 200 g"]


def test_entradas_invalidas():
    with pytest.raises(ErrorValidacion):
        REC.recomendar(-1, 30, N, N)
    with pytest.raises(ErrorValidacion):
        REC.recomendar(10, 0, N, N)


@pytest.mark.parametrize(
    ("tramos", "ft", "mensaje"),
    [
        ((TramoTasa(1, None, 2),), FACTOR_T, "empezar en 0"),
        ((TramoTasa(0, 10, 2), TramoTasa(20, None, 1)), FACTOR_T, "contiguos"),
        ((TramoTasa(0, 10, 2),), FACTOR_T, "último tramo"),
        ((TramoTasa(0, None, 0),), FACTOR_T, "> 0 %"),
        ((TramoTasa(0, None, 1),), {N: 1.0, P: 0.7}, "normal, precaucion y critica"),
        ((TramoTasa(0, None, 1),), {N: 1.5, P: 0.7, C: 0}, "entre 0 y 1"),
    ],
)
def test_tabla_invalida(tramos, ft, mensaje):
    with pytest.raises(ErrorValidacion, match=mensaje):
        TablaAlimentacion(tramos, ft, FACTOR_O)


# --------------------------------------------------------------------------- servicio


@pytest.fixture
def entorno():
    lotes = RepositorioLoteMemoria()
    lotes.guardar(Lote(1, "L-1", 5000, 45.0, 62.0, date(2026, 8, 1), id=1))
    lotes.guardar(Lote(1, "L-0", 10, 1, 1, date(2026, 1, 1), activo=False, id=2))
    lotes._siguiente = 3
    mortalidad = RepositorioMortalidadMemoria()
    mortalidad.guardar(RegistroMortalidad(1, 12, RelojFijo().ahora()))
    lecturas = RepositorioLecturaMemoria()
    srv = ServicioRacion(lotes, mortalidad, lecturas, EvaluadorCalidadAgua(UMBRALES), REC)
    return srv, lecturas


def _lectura(t, od):
    return LecturaAgua(1, t, od, 7.2, FuenteLectura.SENSOR, RelojFijo().ahora())


def test_cp_rf07_01_servicio_usa_biomasa_y_ultima_lectura(entorno):
    """CP-RF07-01: biomasa = 4988 × 62 g = 309.256 kg; T y OD normales -> 2 % = 6.185 kg."""
    srv, lecturas = entorno
    lecturas.guardar(_lectura(12.0, 8.0))
    r = srv.recomendar(1, OPERARIO)
    assert r.peces_vivos == 4988 and r.recomendacion.biomasa_kg == 309.256
    assert r.recomendacion.racion_kg == 6.185 and r.lectura is not None


def test_cp_rf07_02_servicio_suspende_con_oxigeno_critico(entorno):
    """CP-RF07-02: OD 4.5 mg/L (crítico) -> ración 0 kg."""
    srv, lecturas = entorno
    lecturas.guardar(_lectura(17.0, 4.5))
    r = srv.recomendar(1, OPERARIO).recomendacion
    assert r.racion_kg == 0 and r.suspender
    assert (r.nivel_temperatura, r.nivel_oxigeno) == (P, C)


def test_servicio_lote_cerrado_o_inexistente(entorno):
    srv, _ = entorno
    with pytest.raises(Conflicto):
        srv.recomendar(2, OPERARIO)
    with pytest.raises(NoEncontrado):
        srv.recomendar(99, OPERARIO)
    assert srv.recomendar(1, OPERARIO).recomendacion.advertencias  # sin lecturas
