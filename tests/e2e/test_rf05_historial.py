"""E2E RF-05: historial con filtro de fechas, gráfico de tendencia e índice de riesgo
(capturas en evidencias/inc2/)."""

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def _token(api, usuario, password):
    r = api.post("/api/auth/login", json={"nombre_usuario": usuario, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_cp_rf05_01_y_02_historial_tendencia_y_riesgo(pagina, url_base):
    """CP-RF05-01: el filtro muestra solo las lecturas del rango en tabla y gráfico.
    CP-RF05-02: el índice de riesgo se muestra con su semáforo."""
    with httpx.Client(base_url=url_base) as api:
        pisc = _token(api, "piscicultor", "Pisci123!")
        oper = _token(api, "operario", "Oper123!")
        eid = api.post(
            "/api/estanques", json={"nombre": "Estanque Historial"}, headers=pisc
        ).json()["id"]
        datos = [
            ("2026-10-10T06:00:00Z", 11.0, 9.0, 7.0),
            ("2026-10-11T06:00:00Z", 12.0, 8.5, 7.1),
            ("2026-10-11T18:00:00Z", 13.0, 7.9, 7.2),
            ("2026-10-12T06:00:00Z", 14.0, 7.2, 7.3),
            ("2026-10-12T18:00:00Z", 15.5, 6.6, 7.4),
            ("2026-10-13T06:00:00Z", 16.5, 5.8, 7.5),
            ("2026-10-14T06:00:00Z", 17.5, 4.6, 7.6),
        ]
        for medido_en, t, od, ph in datos:
            api.post(
                "/api/lecturas",
                json={
                    "estanque_id": eid,
                    "temperatura_c": t,
                    "oxigeno_mg_l": od,
                    "ph": ph,
                    "medido_en": medido_en,
                },
                headers=oper,
            ).raise_for_status()

    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    pagina.goto(f"/estanques/{eid}/historial")
    pagina.fill("input[name=desde]", "2026-10-11")
    pagina.fill("input[name=hasta]", "2026-10-13")
    capturar(pagina, 2, 5, 1)
    pagina.click("#filtro-fechas button[type=submit]")
    pagina.wait_for_url("**desde=2026-10-11**")
    filas = pagina.locator("#tabla-historial tbody tr")
    assert filas.count() == 5
    assert "13/10/2026" in filas.first.inner_text()
    pagina.locator("#grafico-tendencia[data-listo='1']").wait_for(timeout=10000)
    riesgo = pagina.locator("#riesgo")
    # Última lectura: T 17.5 (precaución) y OD 4.6 (crítico) + 1 alerta crítica abierta = 65.
    assert "65" in riesgo.locator(".valor").inner_text()
    assert "rojo" in riesgo.locator(".semaforo-grande").get_attribute("class")
    capturar(pagina, 2, 5, 2)
