"""RF-10 por la API REST, el panel y el historial."""

from datetime import UTC, datetime, timedelta


def _cargar(cliente, enc, eid, valores_od, fin):
    for i, od in enumerate(valores_od):
        momento = fin - timedelta(hours=len(valores_od) - 1 - i)
        r = cliente.post(
            "/api/lecturas",
            json={
                "estanque_id": eid,
                "temperatura_c": 12.0,
                "oxigeno_mg_l": od,
                "ph": 7.2,
                "medido_en": momento.isoformat(),
            },
            headers=enc,
        )
        assert r.status_code == 201


def test_cp_rf10_01_api_y_panel_muestran_la_prediccion(
    cliente, como_piscicultor, como_operario, reloj
):
    """CP-RF10-01: OD bajando 0.4 mg/L por hora -> crítico en ~2.5 h."""
    eid = cliente.post(
        "/api/estanques", json={"nombre": "E-pred"}, headers=como_piscicultor
    ).json()["id"]
    _cargar(cliente, como_operario, eid, [8.0, 7.6, 7.2, 6.8, 6.4, 6.0], reloj.ahora())
    r = cliente.get(f"/api/estanques/{eid}/prediccion", headers=como_operario).json()
    assert (
        r["principal"]["estado"] == "RIESGO" and r["principal"]["parametro"] == "OXIGENO_DISUELTO"
    )
    assert r["principal"]["horas_hasta_limite"] == 2.5 and r["principal"]["r2"] == 1.0
    panel = cliente.get("/api/panel", headers=como_operario).json()
    estado = next(e for e in panel if e["estanque_id"] == eid)
    assert estado["prediccion"].startswith("Oxígeno disuelto alcanzaría el nivel crítico")
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    hoy = reloj.ahora().date().isoformat()
    html = cliente.get(f"/estanques/{eid}/historial?desde={hoy}&hasta={hoy}").text
    assert "Predicción de tendencia" in html and "en ~2.5 h" in html


def test_cp_rf10_02_datos_insuficientes_sin_error(cliente, como_piscicultor, como_operario):
    """CP-RF10-02: sin lecturas suficientes la API responde 200 con 'datos insuficientes'."""
    eid = cliente.post(
        "/api/estanques", json={"nombre": "E-pocas"}, headers=como_piscicultor
    ).json()["id"]
    _cargar(cliente, como_operario, eid, [8.0, 7.9], datetime(2026, 10, 22, 10, tzinfo=UTC))
    r = cliente.get(f"/api/estanques/{eid}/prediccion", headers=como_operario)
    assert r.status_code == 200
    assert r.json()["principal"]["estado"] == "DATOS_INSUFICIENTES"
    panel = cliente.get("/api/panel", headers=como_operario).json()
    assert next(e for e in panel if e["estanque_id"] == eid)["prediccion"] is None
    assert cliente.get("/api/estanques/999/prediccion", headers=como_operario).status_code == 404
