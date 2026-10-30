"""RF-10: predicción de tendencia por regresión lineal (dominio)."""

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.errores import NoEncontrado
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua, Parametro
from src.domain.model.umbral import Umbral
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.predictor_tendencia import EstadoPrediccion, ajustar, predecir
from src.domain.service.servicio_prediccion import ServicioPrediccion
from tests.fakes import RelojFijo, RepositorioEstanqueMemoria, RepositorioLecturaMemoria
from tests.umbrales import UMBRALES

T0 = datetime(2026, 10, 23, 6, tzinfo=UTC)
OPERARIO = Usuario("o", "Olga", "h", Rol.OPERARIO, RelojFijo().ahora(), id=3)


def serie(valores, paso_h=1.0):
    return [(T0 + timedelta(hours=i * paso_h), v) for i, v in enumerate(valores)]


def test_ajuste_exacto_de_una_recta():
    a = ajustar([0, 1, 2, 3], [8.0, 7.6, 7.2, 6.8])
    assert a.pendiente_por_hora == pytest.approx(-0.4) and a.r2 == pytest.approx(1.0)
    assert ajustar([1, 1, 1], [5, 6, 7]).r2 == 0.0  # sin variación en x


def test_cp_rf10_01_oxigeno_bajando_predice_cruce_del_limite_critico():
    """CP-RF10-01: OD 8.0 -> 6.0 en 5 h (-0.4/h): cruzaría 5 mg/L en 2.5 h."""
    p = predecir(
        Parametro.OXIGENO_DISUELTO, serie([8.0, 7.6, 7.2, 6.8, 6.4, 6.0]), UMBRALES.oxigeno_disuelto
    )
    assert p.estado is EstadoPrediccion.RIESGO and p.limite == 5.0
    assert p.horas_hasta_limite == 2.5 and p.r2 == 1.0
    assert p.momento_estimado == T0 + timedelta(hours=7.5)
    assert "en ~2.5 h" in p.mensaje and "13:30 UTC" in p.mensaje


def test_temperatura_subiendo_predice_cruce_del_limite_alto():
    p = predecir(Parametro.TEMPERATURA, serie([15.0, 15.5, 16.0, 16.5, 17.0]), UMBRALES.temperatura)
    assert p.estado is EstadoPrediccion.RIESGO and p.limite == 18.0 and p.horas_hasta_limite == 2.0


@pytest.mark.parametrize(
    ("valores", "estado"),
    [
        ([8.0, 7.9], EstadoPrediccion.DATOS_INSUFICIENTES),
        ([8.0, 8.0, 8.0, 8.0], EstadoPrediccion.SIN_RIESGO),  # estable
        ([8.0, 7.9, 7.8, 7.7], EstadoPrediccion.SIN_RIESGO),  # cruzaría en 27 h (> 6 h)
        ([8.0, 6.0, 8.2, 6.1, 8.1, 6.2], EstadoPrediccion.SIN_RIESGO),  # ruido: R² bajo
        ([6.0, 5.5, 5.0, 4.5], EstadoPrediccion.YA_CRITICO),
        ([7.0, 7.5, 8.0, 8.5], EstadoPrediccion.SIN_RIESGO),  # mejora
    ],
)
def test_cp_rf10_02_casos_sin_prediccion_de_riesgo(valores, estado):
    """CP-RF10-02: pocos datos, estabilidad, ruido o mejora no generan riesgo ni error."""
    p = predecir(Parametro.OXIGENO_DISUELTO, serie(valores), UMBRALES.oxigeno_disuelto)
    assert p.estado is estado and p.mensaje


def test_servicio_usa_las_24_h_previas_a_la_ultima_lectura():
    estanques = RepositorioEstanqueMemoria()
    eid = estanques.guardar(Estanque("A1", TipoEstanque.ESTANQUE, T0)).id
    lecturas = RepositorioLecturaMemoria()
    srv = ServicioPrediccion(lecturas, estanques, UMBRALES)
    vacio = srv.predecir(eid, OPERARIO)
    assert vacio.basada_en_hasta is None
    assert vacio.principal.estado is EstadoPrediccion.DATOS_INSUFICIENTES
    lecturas.guardar(LecturaAgua(eid, 12, 3.0, 7.2, FuenteLectura.SENSOR, T0 - timedelta(days=3)))
    for i, od in enumerate([8.0, 7.6, 7.2, 6.8, 6.4, 6.0]):
        lecturas.guardar(
            LecturaAgua(eid, 12, od, 7.2, FuenteLectura.SENSOR, T0 + timedelta(hours=i))
        )
    r = srv.predecir(eid, OPERARIO)
    assert r.basada_en_hasta == T0 + timedelta(hours=5)
    assert r.principal.parametro is Parametro.OXIGENO_DISUELTO
    assert r.principal.estado is EstadoPrediccion.RIESGO and r.principal.puntos == 6
    assert len(r.predicciones) == 3
    with pytest.raises(NoEncontrado):
        srv.predecir(99, OPERARIO)


def test_umbral_solo_con_limite_alto():
    solo_max = Umbral(Parametro.TEMPERATURA, "°C", None, 15.0, None, 18.0)
    p = predecir(Parametro.TEMPERATURA, serie([9.0, 8.0, 7.0, 6.0]), solo_max)
    assert p.estado is EstadoPrediccion.SIN_RIESGO
