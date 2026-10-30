"""E2E RF-09: el Administrador emite una clave y un sistema externo consume la API
(capturas en evidencias/inc3/)."""

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def test_cp_rf09_01_y_02_clave_de_integracion(pagina, url_base):
    """CP-RF09-01: con la clave emitida, el sistema externo recibe JSON.
    CP-RF09-02: tras revocarla, la API externa responde 401."""
    iniciar_sesion(pagina, "admin", "Admin123!")
    pagina.wait_for_url("**/panel")
    pagina.goto("/integraciones")
    pagina.fill("#form-clave input[name=nombre]", "ERP Piscigranja")
    capturar(pagina, 3, 9, 1)
    pagina.click("#form-clave button[type=submit]")
    secreto = pagina.locator("#valor-clave").inner_text()
    assert secreto.startswith("ts_")

    with httpx.Client(base_url=url_base) as externo:
        r = externo.get("/api/externa/v1/estanques", headers={"X-API-Key": secreto})
        assert r.status_code == 200
        assert {"Estanque A1", "Estanque A2", "Jaula J1"} <= {e["nombre"] for e in r.json()}
        r = externo.get(
            "/api/externa/v1/estanques/1/lecturas?desde=2026-10-16&hasta=2026-10-22",
            headers={"X-API-Key": secreto},
        )
        assert r.status_code == 200 and len(r.json()) == 56  # lecturas demo del Estanque A1

    pagina.goto("/integraciones")  # muestra el último uso registrado
    capturar(pagina, 3, 9, 2)
    fila = pagina.locator("#tabla-claves tr", has_text="ERP Piscigranja")
    fila.locator("button[type=submit]").click()
    with httpx.Client(base_url=url_base) as externo:
        r = externo.get("/api/externa/v1/estanques", headers={"X-API-Key": secreto})
        assert r.status_code == 401
