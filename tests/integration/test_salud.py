"""La aplicación arranca y expone el endpoint de salud y el contrato OpenAPI."""

from fastapi.testclient import TestClient

from src.main import crear_app


def test_salud_responde_ok():
    r = TestClient(crear_app()).get("/api/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "servicio": "TruchaSmart"}


def test_openapi_exportado_esta_actualizado():
    from tools.export_openapi import main

    assert main(["--check"]) == 0
