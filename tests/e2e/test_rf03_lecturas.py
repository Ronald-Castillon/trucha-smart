"""E2E RF-03: registro manual de lectura y refresco del panel (capturas en evidencias/inc1/)."""

import time

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def test_cp_rf03_01_lectura_manual_visible_en_panel(pagina):
    """CP-RF03-01: el operario registra una lectura y la ve como última en el panel en < 2 s."""
    iniciar_sesion(pagina, "operario", "Oper123!")
    pagina.wait_for_url("**/panel")
    pagina.goto("/lecturas/nueva?estanque_id=1")
    pagina.fill("input[name=temperatura_c]", "13.4")
    pagina.fill("input[name=oxigeno_mg_l]", "8.6")
    pagina.fill("input[name=ph]", "7.6")
    capturar(pagina, 1, 3, 1)
    inicio = time.perf_counter()
    pagina.click("main button[type=submit]")
    tarjeta = pagina.locator('[data-estanque="1"]')
    tarjeta.locator(".oxigeno", has_text="8.60").wait_for(timeout=2000)
    assert time.perf_counter() - inicio < 2.0
    assert tarjeta.locator(".temperatura").inner_text() == "13.40"
    capturar(pagina, 1, 3, 2)


def test_cp_rf03_01_lectura_del_sensor_aparece_sin_recargar(pagina, url_base):
    """CP-RF03-01: una lectura enviada por API (sensor) aparece en el panel abierto en < 2 s."""
    iniciar_sesion(pagina, "operario", "Oper123!")
    pagina.wait_for_url("**/panel")
    with httpx.Client(base_url=url_base) as api:
        token = api.post(
            "/api/auth/login", json={"nombre_usuario": "operario", "password": "Oper123!"}
        ).json()["access_token"]
        inicio = time.perf_counter()
        r = api.post(
            "/api/lecturas",
            json={"estanque_id": 2, "temperatura_c": 11.11, "oxigeno_mg_l": 9.99, "ph": 7.77},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201
    pagina.locator('[data-estanque="2"] .oxigeno', has_text="9.99").wait_for(timeout=2000)
    # El panel consulta cada 1 s: el peor caso es intervalo + latencia de la consulta.
    assert time.perf_counter() - inicio < 2.0


def test_cp_rf03_02_valor_imposible_muestra_error(pagina):
    """CP-RF03-02: pH 15 se rechaza indicando el parámetro."""
    iniciar_sesion(pagina, "operario", "Oper123!")
    pagina.wait_for_url("**/panel")
    pagina.goto("/lecturas/nueva?estanque_id=1")
    pagina.fill("input[name=temperatura_c]", "12")
    pagina.fill("input[name=oxigeno_mg_l]", "8")
    pagina.fill("input[name=ph]", "15")
    pagina.click("main button[type=submit]")
    assert "El pH 15 es físicamente imposible" in pagina.get_by_role("alert").inner_text()
