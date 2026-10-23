"""Prueba de humo E2E: la app arranca y la documentación OpenAPI se renderiza en el navegador."""


def test_documentacion_api_visible(pagina):
    pagina.goto("/docs")
    assert "TruchaSmart" in pagina.title()
