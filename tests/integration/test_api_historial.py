"""RF-05 por la API REST y la web."""

import pytest


@pytest.fixture
def estanque_id(cliente, como_piscicultor, como_operario) -> int:
    eid = cliente.post(
        "/api/estanques", json={"nombre": "E-historial"}, headers=como_piscicultor
    ).json()["id"]
    lecturas = [
        ("2026-10-15T08:00:00Z", 12.0, 8.0, 7.1),
        ("2026-10-16T08:00:00Z", 12.5, 7.8, 7.2),
        ("2026-10-17T08:00:00Z", 13.0, 7.6, 7.3),
        ("2026-10-17T20:00:00Z", 13.5, 6.4, 7.3),
        ("2026-10-18T08:00:00Z", 14.0, 7.4, 7.4),
    ]
    for medido_en, t, od, ph in lecturas:
        r = cliente.post(
            "/api/lecturas",
            json={
                "estanque_id": eid,
                "temperatura_c": t,
                "oxigeno_mg_l": od,
                "ph": ph,
                "medido_en": medido_en,
            },
            headers=como_operario,
        )
        assert r.status_code == 201
    return eid


def test_cp_rf05_01_historial_filtrado_por_fechas(cliente, como_operario, estanque_id):
    """CP-RF05-01: el filtro devuelve solo las lecturas del rango, con niveles y estadísticas."""
    r = cliente.get(
        f"/api/estanques/{estanque_id}/historial?desde=2026-10-16&hasta=2026-10-17",
        headers=como_operario,
    )
    assert r.status_code == 200
    h = r.json()
    assert h["total"] == 3 and h["estanque"] == "E-historial"
    assert [x["medido_en"][:10] for x in h["lecturas"]] == [
        "2026-10-16",
        "2026-10-17",
        "2026-10-17",
    ]
    assert h["lecturas"][-1]["niveles"]["OXIGENO_DISUELTO"] == "PRECAUCION"
    assert h["estadisticas"]["TEMPERATURA"] == {"minimo": 12.5, "maximo": 13.5, "promedio": 13.0}


def test_historial_rango_invertido_da_422(cliente, como_operario, estanque_id):
    r = cliente.get(
        f"/api/estanques/{estanque_id}/historial?desde=2026-10-18&hasta=2026-10-16",
        headers=como_operario,
    )
    assert r.status_code == 422 and r.json()["campo"] == "desde"


def test_cp_rf05_02_riesgo_con_semaforo(cliente, como_operario, estanque_id):
    """CP-RF05-02: riesgo con la última lectura (normal) y luego con OD crítico + alerta."""
    r = cliente.get(f"/api/estanques/{estanque_id}/riesgo", headers=como_operario).json()
    assert (r["valor"], r["semaforo"], r["nivel"]) == (0, "VERDE", "bajo")
    cliente.post(
        "/api/lecturas",
        json={"estanque_id": estanque_id, "temperatura_c": 17, "oxigeno_mg_l": 4.5, "ph": 7.0},
        headers=como_operario,
    )
    r = cliente.get(f"/api/estanques/{estanque_id}/riesgo", headers=como_operario).json()
    # 40 (OD crítico) + 15 (T precaución) + 10 (1 alerta crítica abierta) = 65
    assert (r["valor"], r["semaforo"]) == (65, "ROJO")
    panel = cliente.get("/api/panel", headers=como_operario).json()
    assert next(e for e in panel if e["estanque_id"] == estanque_id)["riesgo"]["valor"] == 65


def test_web_historial_muestra_tabla_grafico_y_semaforo(cliente, estanque_id):
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    r = cliente.get(f"/estanques/{estanque_id}/historial?desde=2026-10-16&hasta=2026-10-18")
    assert r.status_code == 200
    assert r.text.count("<tr>") == (1 + 4) + (1 + 3)  # lecturas 16-18 y estadísticas
    assert "grafico-tendencia" in r.text and "chart.js@4.4.1" in r.text
    assert "semaforo-grande verde" in r.text
    r = cliente.get(f"/estanques/{estanque_id}/historial?desde=2026-10-18&hasta=2026-10-16")
    assert r.status_code == 422 and "posterior" in r.text
    assert "Riesgo 0 · bajo" in cliente.get("/panel").text
