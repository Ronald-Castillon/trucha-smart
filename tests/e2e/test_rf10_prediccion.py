"""E2E RF-10: el panel anticipa que el oxígeno llegará a nivel crítico (evidencias/inc3/)."""

from datetime import UTC, datetime, timedelta

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def test_cp_rf10_01_y_02_prediccion_en_el_panel(pagina, url_base):
    """CP-RF10-02: con pocas lecturas no hay predicción de riesgo.
    CP-RF10-01: con el OD bajando 0.4 mg/L por hora, el panel avisa el cruce en ~2.5 h."""
    with httpx.Client(base_url=url_base) as api:
        r = api.post(
            "/api/auth/login", json={"nombre_usuario": "piscicultor", "password": "Pisci123!"}
        )
        enc = {"Authorization": f"Bearer {r.json()['access_token']}"}
        eid = api.post(
            "/api/estanques", json={"nombre": "Estanque Predicción"}, headers=enc
        ).json()["id"]

        def lectura(od, momento):
            api.post(
                "/api/lecturas",
                json={
                    "estanque_id": eid,
                    "temperatura_c": 12.4,
                    "oxigeno_mg_l": od,
                    "ph": 7.3,
                    "medido_en": momento.isoformat(),
                },
                headers=enc,
            ).raise_for_status()

        ahora = datetime.now(UTC).replace(microsecond=0)
        lectura(8.0, ahora - timedelta(hours=5))
        lectura(7.6, ahora - timedelta(hours=4))

    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    tarjeta = pagina.locator(f'[data-estanque="{eid}"]')
    assert tarjeta.locator(".prediccion").is_hidden()
    capturar(pagina, 3, 10, 1)

    with httpx.Client(base_url=url_base) as api:
        r = api.post("/api/auth/login", json={"nombre_usuario": "operario", "password": "Oper123!"})
        enc = {"Authorization": f"Bearer {r.json()['access_token']}"}
        for i, od in enumerate([7.2, 6.8, 6.4, 6.0]):
            api.post(
                "/api/lecturas",
                json={
                    "estanque_id": eid,
                    "temperatura_c": 12.4,
                    "oxigeno_mg_l": od,
                    "ph": 7.3,
                    "medido_en": (ahora - timedelta(hours=3 - i)).isoformat(),
                },
                headers=enc,
            ).raise_for_status()

    aviso = tarjeta.locator(".prediccion")
    aviso.wait_for(state="visible", timeout=5000)
    assert "alcanzaría el nivel crítico (5) en ~2.5 h" in aviso.inner_text()
    tarjeta.scroll_into_view_if_needed()
    capturar(pagina, 3, 10, 2)
