"""E2E RF-04: alerta crítica en el panel y su atención (capturas en evidencias/inc1/)."""

import time

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def _token(api: httpx.Client) -> dict[str, str]:
    r = api.post("/api/auth/login", json={"nombre_usuario": "operario", "password": "Oper123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_cp_rf04_01_alerta_critica_visible_en_panel(pagina, url_base):
    """CP-RF04-01: una lectura del sensor con OD 4.5 produce una alerta CRÍTICA en el panel
    abierto en < 2 s (incluido el intervalo de refresco de 1 s)."""
    iniciar_sesion(pagina, "operario", "Oper123!")
    pagina.wait_for_url("**/panel")
    tarjeta = pagina.locator('[data-estanque="1"]')
    capturar(pagina, 1, 4, 1)
    with httpx.Client(base_url=url_base) as api:
        inicio = time.perf_counter()
        r = api.post(
            "/api/lecturas",
            json={"estanque_id": 1, "temperatura_c": 12.5, "oxigeno_mg_l": 4.5, "ph": 7.3},
            headers=_token(api),
        )
    assert r.status_code == 201 and r.json()["alertas"][0]["nivel"] == "CRITICA"
    tarjeta.locator(".alerta .etiqueta.CRITICA").wait_for(timeout=2000)
    assert time.perf_counter() - inicio < 2.0
    assert "Oxígeno disuelto en CRÍTICA: 4.50 mg/L" in tarjeta.inner_text()
    assert "nivel-CRITICA" in tarjeta.locator(".oxigeno").get_attribute("class")


def test_cp_rf04_02_operario_atiende_alerta(pagina, url_base):
    """CP-RF04-02: la segunda lectura crítica no duplica la alerta; al atenderla queda
    registrado el usuario y la fecha/hora."""
    with httpx.Client(base_url=url_base) as api:
        enc = _token(api)
        r = api.post(
            "/api/lecturas",
            json={"estanque_id": 1, "temperatura_c": 12.4, "oxigeno_mg_l": 4.3, "ph": 7.3},
            headers=enc,
        )
        assert r.json()["alertas"] == []
        abiertas = api.get("/api/alertas?estado=ABIERTA&estanque_id=1", headers=enc).json()
    criticas = [a for a in abiertas if a["nivel"] == "CRITICA"]
    assert len(criticas) == 1
    alerta_id = criticas[0]["id"]

    iniciar_sesion(pagina, "operario", "Oper123!")
    pagina.wait_for_url("**/panel")
    pagina.goto("/alertas")
    fila = pagina.locator(f'#alertas-abiertas tr[data-alerta="{alerta_id}"]')
    fila.locator("input[name=observacion]").fill("Aireador de emergencia encendido")
    fila.locator("button[type=submit]").click()
    assert f"Alerta {alerta_id} atendida" in pagina.get_by_role("status").inner_text()
    atendida = pagina.locator(f'#alertas-atendidas tr[data-alerta="{alerta_id}"]')
    assert atendida.locator(".atendida-por").inner_text() == "Olga Operaria"
    assert atendida.locator(".atendida-en").inner_text().strip() != ""
    capturar(pagina, 1, 4, 2)
