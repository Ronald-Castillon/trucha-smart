"""RF-12: riesgo de evento crítico estimado por el modelo entrenado (dominio y adaptador)."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.adapters.outbound.ml.modelo_logistico import ModeloLogistico
from src.domain.errores import NoEncontrado
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.riesgo_modelo import (
    CARACTERISTICAS,
    NivelRiesgoModelo,
    ServicioRiesgoModelo,
    caracteristicas,
    nivel_de,
)
from src.ports.outbound.modelo_riesgo import ResultadoModelo
from tests.fakes import RelojFijo, RepositorioEstanqueMemoria, RepositorioLecturaMemoria
from tests.umbrales import UMBRALES

RAIZ = Path(__file__).resolve().parents[2]
MODELO = RAIZ / "models" / "riesgo" / "modelo_v1.json"
T0 = datetime(2026, 10, 23, 6, tzinfo=UTC)
OPERARIO = Usuario("o", "Olga", "h", Rol.OPERARIO, RelojFijo().ahora(), id=3)


def serie(ods, temps=None, paso_h=1.0):
    return [
        (T0 + timedelta(hours=i * paso_h), temps[i] if temps else 12.4, od, 7.3)
        for i, od in enumerate(ods)
    ]


class ModeloFijo:
    version = "fijo-v0"

    def __init__(self, probabilidad, aportes=None):
        self.probabilidad, self.aportes = probabilidad, aportes or {}
        self.recibido = None

    def predecir(self, x):
        self.recibido = x
        return ResultadoModelo(self.probabilidad, self.aportes)


def servicio(modelo, ods, temps=None):
    estanques = RepositorioEstanqueMemoria()
    eid = estanques.guardar(Estanque("A1", TipoEstanque.ESTANQUE, T0)).id
    lecturas = RepositorioLecturaMemoria()
    lecturas.guardar(LecturaAgua(eid, 12, 9.0, 7.2, FuenteLectura.SENSOR, T0 - timedelta(days=3)))
    for m, t, od, ph in serie(ods, temps):
        lecturas.guardar(LecturaAgua(eid, t, od, ph, FuenteLectura.SENSOR, m))
    return ServicioRiesgoModelo(lecturas, estanques, UMBRALES, modelo), eid


def test_caracteristicas_de_la_ventana():
    x = caracteristicas(serie([8.0, 7.6, 7.2, 6.8, 6.4, 6.0]), 5.0, 18.0)
    assert set(x) >= set(CARACTERISTICAS)
    assert x["od_pendiente_6h"] == pytest.approx(-0.4)
    assert x["od_margen"] == pytest.approx(1.0) and x["t_margen"] == pytest.approx(5.6)
    assert x["od_min_24h"] == 6.0 and x["t_max_24h"] == 12.4
    assert caracteristicas(serie([8.0, 7.9, 7.8]), 5.0, 18.0) is None
    assert (
        caracteristicas(serie([8.0, 7.9, 7.8, 7.7], paso_h=7.0), 5.0, 18.0)["od_pendiente_6h"] == 0
    )


@pytest.mark.parametrize(
    ("p", "nivel"),
    [(0.0, "BAJO"), (0.29, "BAJO"), (0.30, "MEDIO"), (0.59, "MEDIO"), (0.60, "ALTO"), (1, "ALTO")],
)
def test_niveles_por_probabilidad(p, nivel):
    assert nivel_de(p) is NivelRiesgoModelo(nivel)


def test_servicio_entrega_nivel_factores_y_version():
    aportes = {"od_margen": 1.5, "od_pendiente_6h": 2.0, "ph_actual": -0.3}
    modelo = ModeloFijo(0.82, {**aportes, "t_margen": 0.1, "t_max_24h": 0.05})
    srv, eid = servicio(modelo, [8.0, 7.6, 7.2, 6.8, 6.4, 6.0])
    r = srv.evaluar(eid, OPERARIO)
    assert r.nivel is NivelRiesgoModelo.ALTO and r.probabilidad == 0.82
    assert [f.nombre for f in r.factores] == [
        "tendencia del oxígeno (6 h)",
        "margen de oxígeno sobre el límite",
        "margen de temperatura bajo el límite",
    ]  # solo aportes positivos, los 3 mayores
    assert r.version_modelo == "fijo-v0" and r.puntos == 6
    assert r.basada_en_hasta == T0 + timedelta(hours=5)
    assert "82 % (ALTO)" in r.mensaje.replace("82%", "82 %")
    assert modelo.recibido["od_margen"] == pytest.approx(1.0)  # la lectura de hace 3 días no entra


def test_servicio_sin_datos_ya_critico_y_estanque_inexistente():
    srv, eid = servicio(ModeloFijo(0.9), [8.0, 7.9])
    r = srv.evaluar(eid, OPERARIO)
    assert r.nivel is NivelRiesgoModelo.DATOS_INSUFICIENTES and r.probabilidad is None
    srv, eid = servicio(ModeloFijo(0.1), [6.0, 5.6, 5.2, 4.8])
    assert srv.evaluar(eid, OPERARIO).nivel is NivelRiesgoModelo.YA_CRITICO
    vacio = ServicioRiesgoModelo(
        RepositorioLecturaMemoria(), RepositorioEstanqueMemoria(), UMBRALES, ModeloFijo(0.1)
    )
    with pytest.raises(NoEncontrado):
        vacio.evaluar(99, OPERARIO)


def test_cp_rf12_01_modelo_real_oxigeno_cayendo_es_alto():
    """CP-RF12-01: OD 8.0 → 6.0 en 5 h con el modelo entrenado: ALTO (≥ 60 %)."""
    srv, eid = servicio(ModeloLogistico.desde_archivo(MODELO), [8.0, 7.6, 7.2, 6.8, 6.4, 6.0])
    r = srv.evaluar(eid, OPERARIO)
    assert r.nivel is NivelRiesgoModelo.ALTO and r.probabilidad >= 0.6
    assert r.factores[0].nombre == "tendencia del oxígeno (6 h)"
    assert r.version_modelo == "riesgo-v1"


def test_cp_rf12_02_modelo_real_estable_es_bajo():
    """CP-RF12-02: lecturas estables en rango normal: BAJO."""
    srv, eid = servicio(ModeloLogistico.desde_archivo(MODELO), [8.2, 8.1, 8.2, 8.3, 8.2, 8.1])
    r = srv.evaluar(eid, OPERARIO)
    assert r.nivel is NivelRiesgoModelo.BAJO and r.probabilidad < 0.3


def test_adaptador_reproduce_las_probabilidades_del_entrenamiento():
    datos = json.loads(MODELO.read_text(encoding="utf-8"))
    modelo = ModeloLogistico(datos)
    assert modelo.version == datos["version"] and datos["caracteristicas"] == list(CARACTERISTICAS)
    for e in datos["ejemplos_verificacion"]:
        assert modelo.predecir(e["x"]).probabilidad == pytest.approx(e["probabilidad"], abs=1e-5)
    with pytest.raises(ValueError):
        ModeloLogistico({**datos, "coeficientes": datos["coeficientes"][:-1]})
