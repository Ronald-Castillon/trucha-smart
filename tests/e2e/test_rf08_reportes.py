"""E2E RF-08: reporte por rango de fechas con descarga PDF y CSV (capturas en evidencias/inc2/)."""

import time

from tests.e2e.conftest import capturar
from tests.e2e.test_rf01_autenticacion import iniciar_sesion


def _generar(pagina, tipo, desde, hasta):
    pagina.goto("/reportes")
    pagina.select_option("select[name=tipo]", tipo)
    pagina.fill("input[name=desde]", desde)
    pagina.fill("input[name=hasta]", hasta)


def _descargar(pagina, selector, carpeta):
    inicio = time.perf_counter()
    with pagina.expect_download() as descarga:
        pagina.click(selector)
    ruta = carpeta / descarga.value.suggested_filename
    descarga.value.save_as(ruta)
    return ruta, time.perf_counter() - inicio


def test_cp_rf08_01_y_02_descargar_pdf_y_csv(pagina, tmp_path):
    """CP-RF08-01: CSV con encabezados y las filas del rango en < 5 s.
    CP-RF08-02: PDF válido en < 5 s."""
    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    # Rango con los datos demo de db/seed.sql (16 al 22 de octubre de 2026).
    _generar(pagina, "calidad-agua", "2026-10-16", "2026-10-22")
    capturar(pagina, 2, 8, 1)
    pagina.click("#form-reporte button[type=submit]")
    pagina.wait_for_url("**/reportes/vista**")
    assert "Jaula J1" in pagina.locator("#resumen-reporte").inner_text()

    pdf, segundos = _descargar(pagina, "#descargar-pdf", tmp_path)
    assert segundos < 5
    assert pdf.name == "truchasmart_calidad-agua_2026-10-16_2026-10-22.pdf"
    assert pdf.read_bytes().startswith(b"%PDF")

    csv_ruta, segundos = _descargar(pagina, "#descargar-csv", tmp_path)
    assert segundos < 5
    lineas = csv_ruta.read_text(encoding="utf-8-sig").splitlines()
    assert lineas[0].startswith("estanque,medido_en_utc,temperatura_c")
    # Las 168 lecturas del seed en ese rango (Issue #19), más las que agreguen otras E2E.
    assert len(lineas) - 1 >= 168
    total = int(pagina.locator("#total-filas strong").inner_text())
    assert total == len(lineas) - 1
    capturar(pagina, 2, 8, 2)


def test_cp_rf08_02_rango_invertido(pagina):
    """CP-RF08-02: desde > hasta muestra el error y no genera el reporte."""
    iniciar_sesion(pagina, "piscicultor", "Pisci123!")
    pagina.wait_for_url("**/panel")
    _generar(pagina, "produccion", "2026-10-22", "2026-10-16")
    pagina.click("#form-reporte button[type=submit]")
    assert "posterior" in pagina.get_by_role("alert").inner_text()
