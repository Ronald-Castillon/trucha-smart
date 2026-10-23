"""E2E de la interfaz en vivo (Issue #23). El nombre del archivo hace que corra después de las
E2E de los RF, para que sus estanques de prueba no aparezcan en las capturas de evidencia.
Simulador desde la web, gráficos, avisos y auto-refresco; captura en evidencias/mejoras/."""

from contextlib import contextmanager

import httpx

from tests.e2e.conftest import EVIDENCIAS
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


@contextmanager
def _api(url_base, usuario, password):
    with httpx.Client(base_url=url_base) as api:
        r = api.post("/api/auth/login", json={"nombre_usuario": usuario, "password": password})
        api.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
        yield api


def test_panel_en_vivo_con_simulador_web(pagina, url_base):
    with _api(url_base, "piscicultor", "Pisci123!") as api:
        eid = api.post("/api/estanques", json={"nombre": "Estanque En Vivo"}).json()["id"]
    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    tarjeta = pagina.locator(f'[data-estanque="{eid}"]')
    tarjeta.locator("canvas.sparkline[data-listo='1']").wait_for(timeout=10000)

    tarjeta.locator(".sim-escenario").select_option("critico_oxigeno")
    tarjeta.locator(".sim-boton").click()
    tarjeta.locator(".sim-boton", has_text="Detener").wait_for(timeout=5000)
    # 8.0 -> 6.8 mg/L en 3 lecturas (cada 2 s): aparece el aviso emergente de precaución.
    aviso = pagina.locator("#avisos .aviso.precaucion", has_text="Estanque En Vivo")
    aviso.wait_for(timeout=15000)
    assert "PRECAUCIÓN" in aviso.inner_text()
    assert tarjeta.locator(".alerta .etiqueta.PRECAUCION").count() == 1
    destino = EVIDENCIAS / "mejoras" / "panel_en_vivo.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    pagina.screenshot(path=str(destino), full_page=True)

    tarjeta.locator(".sim-boton").click()
    tarjeta.locator(".sim-boton", has_text="Simular").wait_for(timeout=5000)
    with _api(url_base, "operario", "Oper123!") as api:
        assert api.get("/api/simulador").json() == []


def test_lista_de_alertas_se_actualiza_sola(pagina, url_base):
    with _api(url_base, "piscicultor", "Pisci123!") as api:
        eid = api.post("/api/estanques", json={"nombre": "Estanque Alertas Vivo"}).json()["id"]
    iniciar_sesion(pagina, "operario", "Oper123!")
    pagina.wait_for_url("**/panel")
    pagina.goto("/alertas")
    with _api(url_base, "operario", "Oper123!") as api:
        r = api.post(
            "/api/lecturas",
            json={"estanque_id": eid, "temperatura_c": 19.5, "oxigeno_mg_l": 8, "ph": 7.2},
        )
        alerta_id = r.json()["alertas"][0]["id"]
    # Sin recargar: la fila nueva aparece y además se muestra el aviso emergente.
    pagina.locator(f'#alertas-abiertas tr[data-alerta="{alerta_id}"]').wait_for(timeout=8000)
    pagina.locator("#avisos .aviso.critica", has_text="Estanque Alertas Vivo").wait_for(
        timeout=8000
    )
