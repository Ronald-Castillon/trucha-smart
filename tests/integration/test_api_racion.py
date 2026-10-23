"""RF-07 por la API REST y la web."""

from pathlib import Path

import pytest

from src.adapters.config import RAIZ, cargar_alimentacion
from src.domain.errores import ErrorValidacion
from tests.unit.test_racion import TABLA


@pytest.fixture
def ids(cliente, como_piscicultor) -> tuple[int, int]:
    eid = cliente.post(
        "/api/estanques", json={"nombre": "E-racion"}, headers=como_piscicultor
    ).json()["id"]
    lote = cliente.post(
        f"/api/estanques/{eid}/lotes",
        json={
            "codigo": "L-R1",
            "num_peces": 5000,
            "peso_medio_g": 62,
            "fecha_siembra": "2026-08-01",
        },
        headers=como_piscicultor,
    ).json()
    return eid, lote["id"]


def _lectura(cliente, enc, eid, t, od):
    r = cliente.post(
        "/api/lecturas",
        json={"estanque_id": eid, "temperatura_c": t, "oxigeno_mg_l": od, "ph": 7.2},
        headers=enc,
    )
    assert r.status_code == 201


def test_config_alimentacion_yaml_coincide_con_la_referencia():
    assert cargar_alimentacion(RAIZ / "config" / "alimentacion.yaml") == TABLA


def test_config_alimentacion_invalida(tmp_path: Path):
    malo = tmp_path / "a.yaml"
    malo.write_text(
        (RAIZ / "config" / "alimentacion.yaml")
        .read_text(encoding="utf-8")
        .replace("{desde_g: 10,  hasta_g: 50", "{desde_g: 12,  hasta_g: 50"),
        encoding="utf-8",
    )
    with pytest.raises(ErrorValidacion, match="contiguos"):
        cargar_alimentacion(malo)


def test_cp_rf07_01_racion_y_regla(cliente, como_operario, ids):
    """CP-RF07-01: 5000 × 62 g = 310 kg × 2 %; T precaución (×0.7) -> 4.34 kg."""
    eid, lote_id = ids
    _lectura(cliente, como_operario, eid, 12.0, 8.0)
    r = cliente.get(f"/api/lotes/{lote_id}/racion", headers=como_operario).json()
    assert (r["biomasa_kg"], r["tasa_pct"], r["racion_kg"], r["suspender"]) == (
        310.0,
        2.0,
        6.2,
        False,
    )
    assert "× 2 % (peso medio 62 g, tramo 50–200 g)" in r["regla"]
    _lectura(cliente, como_operario, eid, 17.0, 8.0)
    r = cliente.get(f"/api/lotes/{lote_id}/racion", headers=como_operario).json()
    assert (r["nivel_temperatura"], r["factor_temperatura"], r["racion_kg"]) == (
        "PRECAUCION",
        0.7,
        4.34,
    )


def test_cp_rf07_02_oxigeno_critico_suspende(cliente, como_operario, ids):
    """CP-RF07-02: OD crítico -> ración 0 y 'Suspender alimentación'."""
    eid, lote_id = ids
    _lectura(cliente, como_operario, eid, 12.0, 4.5)
    r = cliente.get(f"/api/lotes/{lote_id}/racion", headers=como_operario).json()
    assert r["racion_kg"] == 0 and r["suspender"] is True
    assert r["regla"].startswith("Suspender alimentación: oxígeno disuelto en nivel CRÍTICO")


def test_racion_sin_lecturas_y_lote_inexistente(cliente, como_operario, ids):
    _, lote_id = ids
    r = cliente.get(f"/api/lotes/{lote_id}/racion", headers=como_operario).json()
    assert r["lectura_id"] is None and r["advertencias"]
    assert cliente.get("/api/lotes/999/racion", headers=como_operario).status_code == 404


def test_web_muestra_racion(cliente, como_operario, ids):
    eid, lote_id = ids
    _lectura(cliente, como_operario, eid, 12.0, 8.0)
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    r = cliente.get(f"/lotes/{lote_id}/produccion")
    assert 'id="racion-kg">6.200<' in r.text and "Ración = 310.000 kg" in r.text
