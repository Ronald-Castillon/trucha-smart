"""E2E RF-12: el historial muestra el riesgo estimado por el modelo de IA (evidencias/inc4/)."""

from datetime import UTC, datetime, timedelta

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def test_cp_rf12_01_y_02_riesgo_del_modelo_en_el_historial(pagina, url_base):
    """CP-RF12-02: con lecturas estables el modelo estima riesgo BAJO.
    CP-RF12-01: cuando el OD empieza a caer 0.4 mg/L por hora, el riesgo pasa a ALTO."""
    ahora = datetime.now(UTC).replace(microsecond=0)
    with httpx.Client(base_url=url_base) as api:
        r = api.post(
            "/api/auth/login", json={"nombre_usuario": "piscicultor", "password": "Pisci123!"}
        )
        enc = {"Authorization": f"Bearer {r.json()['access_token']}"}
        eid = api.post("/api/estanques", json={"nombre": "Estanque IA"}, headers=enc).json()["id"]

        def lectura(od, momento):
            api.post(
                "/api/lecturas",
                json={"estanque_id": eid, "temperatura_c": 12.4, "oxigeno_mg_l": od, "ph": 7.3,
                      "medido_en": momento.isoformat()},
                headers=enc,
            ).raise_for_status()  # fmt: skip

        for i, od in enumerate([8.2, 8.1, 8.2, 8.3, 8.2, 8.1]):
            lectura(od, ahora - timedelta(hours=11 - i))
        iniciar_sesion(pagina, "piscicultor", "Pisci123!")
        pagina.wait_for_url("**/panel")
        hoy = ahora.date().isoformat()
        ayer = (ahora - timedelta(days=1)).date().isoformat()
        historial = f"/estanques/{eid}/historial?desde={ayer}&hasta={hoy}"
        pagina.goto(historial)
        mensaje = pagina.locator("#riesgo-modelo-mensaje")
        assert "(BAJO)" in mensaje.inner_text()
        pagina.locator("#riesgo-modelo").scroll_into_view_if_needed()
        capturar(pagina, 4, 12, 1)

        for i, od in enumerate([7.8, 7.4, 7.0, 6.6, 6.2]):
            lectura(od, ahora - timedelta(hours=4 - i))
    pagina.goto(historial)
    assert "(ALTO)" in mensaje.inner_text()
    assert "tendencia del oxígeno" in pagina.locator("#riesgo-modelo-factores").inner_text()
    pagina.locator("#riesgo-modelo").scroll_into_view_if_needed()
    capturar(pagina, 4, 12, 2)
