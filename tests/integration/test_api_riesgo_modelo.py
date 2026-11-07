"""RF-12 por la API REST y el historial web."""

from datetime import timedelta


def _cargar(cliente, enc, eid, valores_od, fin):
    for i, od in enumerate(valores_od):
        r = cliente.post(
            "/api/lecturas",
            json={
                "estanque_id": eid,
                "temperatura_c": 12.4,
                "oxigeno_mg_l": od,
                "ph": 7.3,
                "medido_en": (fin - timedelta(hours=len(valores_od) - 1 - i)).isoformat(),
            },
            headers=enc,
        )
        assert r.status_code == 201


def test_cp_rf12_01_api_e_historial_con_riesgo_alto(
    cliente, como_piscicultor, como_operario, reloj
):
    eid = cliente.post("/api/estanques", json={"nombre": "E-ia"}, headers=como_piscicultor).json()[
        "id"
    ]
    _cargar(cliente, como_operario, eid, [8.0, 7.6, 7.2, 6.8, 6.4, 6.0], reloj.ahora())
    r = cliente.get(f"/api/estanques/{eid}/riesgo-modelo", headers=como_operario).json()
    assert r["nivel"] == "ALTO" and r["probabilidad"] >= 0.6
    assert r["version_modelo"] == "riesgo-v1" and r["factores"]
    assert "datos sintéticos" in r["aviso"]
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    hoy = reloj.ahora().date().isoformat()
    html = cliente.get(f"/estanques/{eid}/historial?desde={hoy}&hasta={hoy}").text
    assert "Riesgo estimado por el modelo de IA" in html and "(ALTO)" in html


def test_cp_rf12_02_api_bajo_datos_insuficientes_y_404(
    cliente, como_piscicultor, como_operario, reloj
):
    eid = cliente.post(
        "/api/estanques", json={"nombre": "E-ia-estable"}, headers=como_piscicultor
    ).json()["id"]
    url = f"/api/estanques/{eid}/riesgo-modelo"
    assert cliente.get(url, headers=como_operario).json()["nivel"] == "DATOS_INSUFICIENTES"
    _cargar(cliente, como_operario, eid, [8.2, 8.1, 8.2, 8.3, 8.2, 8.1], reloj.ahora())
    r = cliente.get(url, headers=como_operario)
    assert r.status_code == 200 and r.json()["nivel"] == "BAJO"
    assert cliente.get("/api/estanques/999/riesgo-modelo", headers=como_operario).status_code == 404
    assert cliente.get(url).status_code == 401
