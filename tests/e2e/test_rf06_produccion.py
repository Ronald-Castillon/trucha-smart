"""E2E RF-06: alimentación, mortalidad, biomasa y FCR (capturas en evidencias/inc2/)."""

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def _crear_lote(url_base, nombre, codigo, peces=2000, peso=40.0):
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
                "num_peces": peces,
                "peso_medio_g": peso,
                "fecha_siembra": "2026-09-15",
            },
            headers=enc,
        ).json()
        return lote["id"], enc


def test_cp_rf06_02_fcr_no_calculable_sin_ganancia(pagina, url_base):
    """CP-RF06-02: un lote recién sembrado (ganancia 0) muestra FCR "no calculable"."""
    lote_id, _ = _crear_lote(url_base, "Estanque FCR 0", "L-E2E-F0")
    iniciar_sesion(pagina, "operario", "Oper123!")
    pagina.wait_for_url("**/panel")
    pagina.goto(f"/lotes/{lote_id}/produccion")
    assert pagina.locator("#fcr").inner_text() == "no calculable"


def test_cp_rf06_01_registrar_alimentacion_y_mortalidad(pagina, url_base):
    """CP-RF06-01: el operario registra alimento y mortalidad; se ven biomasa y FCR."""
    lote_id, enc = _crear_lote(url_base, "Estanque Producción", "L-E2E-P1")
    with httpx.Client(base_url=url_base) as api:  # biometría: 40 g -> 52 g
        api.put(f"/api/lotes/{lote_id}/peso", json={"peso_medio_g": 52}, headers=enc)
    iniciar_sesion(pagina, "operario", "Oper123!")
    pagina.wait_for_url("**/panel")
    pagina.goto(f"/lotes/{lote_id}/produccion")
    pagina.fill("#form-alimentacion input[name=cantidad_kg]", "27.5")
    pagina.fill("#form-mortalidad input[name=cantidad]", "20")
    pagina.fill("#form-mortalidad input[name=causa]", "Estrés térmico")
    capturar(pagina, 2, 6, 1)
    pagina.click("#form-alimentacion button[type=submit]")
    assert "Alimentación de 27.5 kg registrada" in pagina.get_by_role("status").inner_text()
    pagina.fill("#form-mortalidad input[name=cantidad]", "20")
    pagina.fill("#form-mortalidad input[name=causa]", "Estrés térmico")
    pagina.click("#form-mortalidad button[type=submit]")
    assert "Mortalidad de 20 peces registrada" in pagina.get_by_role("status").inner_text()
    # vivos 1980 × 52 g = 102.96 kg; inicial 2000 × 40 g = 80 kg; ganancia 22.96 kg
    assert pagina.locator("#biomasa").inner_text() == "102.960 kg"
    assert pagina.locator("#ganancia").inner_text() == "22.960 kg"
    assert pagina.locator("#fcr").inner_text() == "1.20"  # 27.5 / 22.96
    capturar(pagina, 2, 6, 2)
