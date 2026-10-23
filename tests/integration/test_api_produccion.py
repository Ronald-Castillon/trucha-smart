"""RF-06 por la API REST y la web."""

import pytest


@pytest.fixture
def lote_id(cliente, como_piscicultor) -> int:
    eid = cliente.post(
        "/api/estanques", json={"nombre": "E-produccion"}, headers=como_piscicultor
    ).json()["id"]
    lote = cliente.post(
        f"/api/estanques/{eid}/lotes",
        json={
            "codigo": "L-P1",
            "num_peces": 1000,
            "peso_medio_g": 50,
            "fecha_siembra": "2026-09-01",
        },
        headers=como_piscicultor,
    ).json()
    return lote["id"]


def test_cp_rf06_01_alimentacion_mortalidad_biomasa_y_fcr(
    cliente, como_operario, como_piscicultor, lote_id
):
    """CP-RF06-01: biomasa = vivos × peso medio y FCR = alimento / ganancia."""
    for kg in (20.0, 15.04):
        r = cliente.post(
            f"/api/lotes/{lote_id}/alimentacion", json={"cantidad_kg": kg}, headers=como_operario
        )
        assert r.status_code == 201
    r = cliente.post(
        f"/api/lotes/{lote_id}/mortalidad",
        json={"cantidad": 10, "causa": "Manipulación"},
        headers=como_operario,
    )
    assert r.status_code == 201 and r.json()["causa"] == "Manipulación"
    cliente.put(f"/api/lotes/{lote_id}/peso", json={"peso_medio_g": 80}, headers=como_piscicultor)
    p = cliente.get(f"/api/lotes/{lote_id}/produccion", headers=como_operario).json()
    assert (p["peces_vivos"], p["biomasa_kg"], p["ganancia_biomasa_kg"]) == (990, 79.2, 29.2)
    assert (p["alimento_total_kg"], p["fcr"], p["fcr_texto"]) == (35.04, 1.2, "1.20")
    assert len(cliente.get(f"/api/lotes/{lote_id}/alimentacion", headers=como_operario).json()) == 2
    assert (
        cliente.get(f"/api/lotes/{lote_id}/mortalidad", headers=como_operario).json()[0]["cantidad"]
        == 10
    )


def test_cp_rf06_02_fcr_no_calculable_sin_error(cliente, como_operario, lote_id):
    """CP-RF06-02: sin ganancia de biomasa el FCR es "no calculable" y la respuesta es 200."""
    cliente.post(
        f"/api/lotes/{lote_id}/alimentacion", json={"cantidad_kg": 5}, headers=como_operario
    )
    r = cliente.get(f"/api/lotes/{lote_id}/produccion", headers=como_operario)
    assert r.status_code == 200
    assert r.json()["fcr"] is None and r.json()["fcr_texto"] == "no calculable"


@pytest.mark.parametrize(
    ("ruta", "cuerpo", "campo"),
    [
        ("alimentacion", {"cantidad_kg": 0}, "cantidad_kg"),
        ("mortalidad", {"cantidad": 0}, "cantidad"),
        ("mortalidad", {"cantidad": 1001}, "cantidad"),
    ],
)
def test_validaciones_dan_422(cliente, como_operario, lote_id, ruta, cuerpo, campo):
    r = cliente.post(f"/api/lotes/{lote_id}/{ruta}", json=cuerpo, headers=como_operario)
    assert r.status_code == 422 and r.json()["campo"] == campo


def test_lote_inexistente_da_404(cliente, como_operario):
    r = cliente.post("/api/lotes/999/alimentacion", json={"cantidad_kg": 1}, headers=como_operario)
    assert r.status_code == 404


def test_web_produccion(cliente, lote_id):
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    r = cliente.get(f"/lotes/{lote_id}/produccion")
    assert r.status_code == 200 and "no calculable" in r.text
    r = cliente.post(f"/lotes/{lote_id}/alimentacion", data={"cantidad_kg": "12,5"})
    assert "Alimentación de 12.5 kg registrada" in r.text and "12.500 kg" in r.text
    r = cliente.post(f"/lotes/{lote_id}/mortalidad", data={"cantidad": "abc"})
    assert r.status_code == 422 and "cantidad debe ser numérico" in r.text
    r = cliente.post(f"/lotes/{lote_id}/mortalidad", data={"cantidad": "5", "causa": "Estrés"})
    assert "Mortalidad de 5 peces registrada" in r.text and "995 (99.50 %)" in r.text
