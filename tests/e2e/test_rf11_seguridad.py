"""E2E RF-11: bloqueo tras 3 intentos fallidos y bitácora de seguridad (evidencias/inc3/).

Usa un usuario propio para no bloquear a los usuarios demo que usan las demás pruebas E2E.
"""

import httpx

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def test_cp_rf11_01_y_02_bloqueo_y_auditoria(pagina, url_base):
    """CP-RF11-01: el tercer intento fallido bloquea la cuenta (aviso en pantalla, 423).
    CP-RF11-02: el Administrador ve los intentos y el bloqueo en la bitácora, sin contraseñas."""
    with httpx.Client(base_url=url_base) as api:
        r = api.post("/api/auth/login", json={"nombre_usuario": "admin", "password": "Admin123!"})
        enc = {"Authorization": f"Bearer {r.json()['access_token']}"}
        api.post(
            "/api/usuarios",
            json={
                "nombre_usuario": "turno.noche",
                "nombre_completo": "Operario Turno Noche",
                "password": "Noche123!",
                "rol": "OPERARIO",
            },
            headers=enc,
        ).raise_for_status()

    for _ in range(3):
        iniciar_sesion(pagina, "turno.noche", "Adivinada1")
    aviso = pagina.locator(".mensaje.error")
    assert "Cuenta bloqueada por intentos fallidos" in aviso.inner_text()
    iniciar_sesion(pagina, "turno.noche", "Noche123!")  # la correcta tampoco entra
    assert "Cuenta bloqueada" in pagina.locator(".mensaje.error").inner_text()
    capturar(pagina, 3, 11, 1)

    iniciar_sesion(pagina, "admin", "Admin123!")
    pagina.wait_for_url("**/panel")
    pagina.click("nav >> text=Auditoría")
    pagina.wait_for_url("**/auditoria")
    tabla = pagina.locator("#tabla-auditoria")
    filas = tabla.locator("tbody tr")
    assert filas.filter(has_text="turno.noche").count() >= 5
    assert tabla.locator('tr[data-tipo="CUENTA_BLOQUEADA"]').count() >= 1
    assert "Adivinada1" not in tabla.inner_text() and "Noche123!" not in tabla.inner_text()
    capturar(pagina, 3, 11, 2)
