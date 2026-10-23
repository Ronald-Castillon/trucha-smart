"""E2E RF-07: recomendación de ración según biomasa y calidad de agua
(capturas en evidencias/inc2/)."""

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def _preparar(url_base, nombre, codigo):
    with httpx.Client(base_url=url_base) as api:
        r = api.post(
            "/api/auth/login", json={"nombre_usuario": "piscicultor", "password": "Pisci123!"}
        )
        enc = {"Authorization": f"Bearer {r.json()['access_token']}"}
        eid = api.post("/api/estanques", json={"nombre": nombre}, headers=enc).json()["id"]
        lote = api.post(
            f"/api/estanques/{eid}/lotes",
            json={
                "codigo": codigo,
                "num_peces": 3000,
                "peso_medio_g": 120,
                "fecha_siembra": "2026-07-01",
            },
            headers=enc,
        ).json()
        return eid, lote["id"]


def _registrar_lectura(pagina, eid, t, od):
    pagina.goto(f"/lecturas/nueva?estanque_id={eid}")
    pagina.fill("input[name=temperatura_c]", str(t))
    pagina.fill("input[name=oxigeno_mg_l]", str(od))
    pagina.fill("input[name=ph]", "7.3")


def test_cp_rf07_01_racion_con_temperatura_en_precaucion(pagina, url_base):
    """CP-RF07-01: biomasa 3000 × 120 g = 360 kg × 2 % × 0.7 (T 17 °C precaución) = 5.04 kg."""
    eid, lote_id = _preparar(url_base, "Estanque Ración", "L-E2E-R1")
    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    _registrar_lectura(pagina, eid, 17, 8.2)
    capturar(pagina, 2, 7, 1)
    pagina.click("main button[type=submit]")
    pagina.goto(f"/lotes/{lote_id}/produccion")
    assert pagina.locator("#racion-kg").inner_text() == "5.040"
    regla = pagina.locator("#racion-regla").inner_text()
    assert "360.000 kg de biomasa × 2 %" in regla and "× 0.7 (temperatura PRECAUCIÓN)" in regla
    capturar(pagina, 2, 7, 2)


def test_cp_rf07_02_oxigeno_critico_suspende_alimentacion(pagina, url_base):
    """CP-RF07-02: OD 4.2 mg/L -> 0 kg y 'suspender alimentación'."""
    eid, lote_id = _preparar(url_base, "Estanque Ración Crítica", "L-E2E-R2")
    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    _registrar_lectura(pagina, eid, 12, 4.2)
    pagina.click("main button[type=submit]")
    pagina.goto(f"/lotes/{lote_id}/produccion")
    assert pagina.locator("#racion-kg").inner_text() == "0.000"
    assert "suspender alimentación" in pagina.locator("#racion").inner_text()
