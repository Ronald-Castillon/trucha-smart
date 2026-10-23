"""E2E RF-02: crear estanque y sembrar lote (capturas en evidencias/inc1/)."""

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def test_cp_rf02_01_crear_estanque_y_sembrar_lote(pagina):
    """CP-RF02-01: el piscicultor crea un estanque y siembra un lote; aparece en el listado."""
    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    pagina.goto("/estanques")
    pagina.fill("input[name=nombre]", "Estanque E2E")
    pagina.fill("input[name=volumen_m3]", "90")
    pagina.fill("input[name=ubicacion]", "Sector demo")
    pagina.click("form[action='/estanques'] button[type=submit]")
    pagina.get_by_role("link", name="Estanque E2E").click()
    pagina.fill("input[name=codigo]", "L-E2E-01")
    pagina.fill("input[name=num_peces]", "4000")
    pagina.fill("input[name=peso_medio_g]", "15")
    capturar(pagina, 1, 2, 1)
    pagina.click("form[action$='/lotes'] button[type=submit]")
    assert "Lote L-E2E-01 sembrado" in pagina.get_by_role("status").inner_text()
    pagina.goto("/estanques")
    fila = pagina.locator("#tabla-estanques tr", has_text="Estanque E2E")
    assert "L-E2E-01" in fila.inner_text() and "4000" in fila.inner_text()
    capturar(pagina, 1, 2, 2)


def test_cp_rf02_02_lote_con_cero_peces_es_rechazado(pagina):
    """CP-RF02-02: n.º de peces 0 muestra el error del campo y no siembra."""
    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    pagina.goto("/estanques")
    pagina.fill("input[name=nombre]", "Estanque Vacío")
    pagina.click("form[action='/estanques'] button[type=submit]")
    pagina.get_by_role("link", name="Estanque Vacío").click()
    pagina.fill("input[name=codigo]", "L-E2E-00")
    pagina.fill("input[name=num_peces]", "0")
    pagina.fill("input[name=peso_medio_g]", "15")
    pagina.click("form[action$='/lotes'] button[type=submit]")
    assert "número de peces debe ser mayor que 0" in pagina.get_by_role("alert").inner_text()
    assert "no tiene lote activo" in pagina.locator("#lote-activo").inner_text()
