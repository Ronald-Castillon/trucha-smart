"""E2E RF-01: inicio de sesión web con roles (capturas en evidencias/inc1/)."""

from tests.e2e.conftest import capturar


def iniciar_sesion(pagina, usuario: str, password: str) -> None:
    pagina.goto("/login")
    pagina.fill("input[name=nombre_usuario]", usuario)
    pagina.fill("input[name=password]", password)
    pagina.click("button[type=submit]")


def test_cp_rf01_02_credenciales_invalidas_muestran_mensaje(pagina):
    """CP-RF01-02: credenciales inválidas muestran 'Usuario o contraseña incorrectos'."""
    iniciar_sesion(pagina, "operario", "incorrecta")
    alerta = pagina.get_by_role("alert")
    assert alerta.inner_text() == "Usuario o contraseña incorrectos"
    assert pagina.url.endswith("/login")


def test_cp_rf01_01_login_operario_llega_al_panel(pagina):
    """CP-RF01-01: un Operario inicia sesión y ve el panel con su rol; sin menú de usuarios."""
    pagina.goto("/login")
    pagina.fill("input[name=nombre_usuario]", "operario")
    pagina.fill("input[name=password]", "Oper123!")
    capturar(pagina, 1, 1, 1)
    pagina.click("button[type=submit]")
    pagina.wait_for_url("**/panel")
    assert "Operario" in pagina.locator("#usuario-actual").inner_text()
    assert pagina.get_by_role("link", name="Usuarios").count() == 0
    capturar(pagina, 1, 1, 2)
