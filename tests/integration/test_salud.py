"""La aplicación arranca y expone el endpoint de salud y el contrato OpenAPI."""

from fastapi.testclient import TestClient

from src.main import crear_app


def test_salud_responde_ok(cliente):
    r = cliente.get("/api/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "servicio": "TruchaSmart", "base_datos": "ok"}


def test_salud_responde_503_sin_caerse_si_la_bd_no_esta(recursos, tmp_path):
    """RNF-R: con la base de datos inaccesible la API sigue respondiendo e informa 503."""
    from dataclasses import replace

    from src.adapters.outbound.persistence.db import BaseDatos

    caida = replace(recursos, bd=BaseDatos(f"sqlite:///{(tmp_path / 'no/existe/x.db').as_posix()}"))
    cliente = TestClient(crear_app(recursos=caida))
    r = cliente.get("/api/salud")
    assert r.status_code == 503 and r.json()["base_datos"] == "no disponible"
    assert cliente.get("/api/salud").status_code == 503  # sigue vivo


def test_openapi_exportado_esta_actualizado():
    from tools.export_openapi import main

    assert main(["--check"]) == 0
