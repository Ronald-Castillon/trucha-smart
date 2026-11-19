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


# --- RFC #63 (defecto #51): /api/salud no espera más que su tiempo máximo -----------------


def _servidor_mudo():
    """Servidor TCP que acepta conexiones y nunca responde (como el proxy de Docker Desktop)."""
    import socket
    import threading

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen()
    aceptadas = []

    def aceptar():
        while True:
            try:
                aceptadas.append(srv.accept()[0])
            except OSError:
                return

    threading.Thread(target=aceptar, daemon=True).start()
    return srv, aceptadas


def test_salud_responde_503_rapido_si_la_bd_acepta_y_no_responde(recursos):
    """CP-RFC63-01: con una BD que no contesta, /api/salud da 503 en menos de 2 s (antes > 4 s)."""
    import time
    from dataclasses import replace

    from src.adapters.outbound.persistence.db import BaseDatos

    srv, aceptadas = _servidor_mudo()
    try:
        puerto = srv.getsockname()[1]
        muda = BaseDatos(f"postgresql+psycopg://u:p@127.0.0.1:{puerto}/x", salud_timeout_s=1.0)
        cliente = TestClient(crear_app(recursos=replace(recursos, bd=muda)))
        inicio = time.monotonic()
        r = cliente.get("/api/salud")
        assert r.status_code == 503 and r.json()["base_datos"] == "no disponible"
        assert time.monotonic() - inicio < 2.0
        # Mientras la sonda anterior sigue colgada, la siguiente responde de inmediato.
        inicio = time.monotonic()
        assert cliente.get("/api/salud").status_code == 503
        assert time.monotonic() - inicio < 0.5
    finally:
        srv.close()
        for c in aceptadas:
            c.close()


def test_salud_timeout_es_configurable(monkeypatch):
    """CP-RFC63-02: SALUD_TIMEOUT_S ajusta el tiempo máximo; por defecto es 1 s."""
    from src.adapters.config import Configuracion

    monkeypatch.delenv("SALUD_TIMEOUT_S", raising=False)
    assert Configuracion.desde_entorno().salud_timeout_s == 1.0
    monkeypatch.setenv("SALUD_TIMEOUT_S", "2.5")
    assert Configuracion.desde_entorno().salud_timeout_s == 2.5
