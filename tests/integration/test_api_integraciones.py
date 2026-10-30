"""RF-09 por la API REST y la web."""

import pytest


@pytest.fixture
def estanque_id(cliente, como_piscicultor, como_operario) -> int:
    eid = cliente.post(
        "/api/estanques", json={"nombre": "E-externa"}, headers=como_piscicultor
    ).json()["id"]
    cliente.post(
        "/api/lecturas",
        json={
            "estanque_id": eid,
            "temperatura_c": 12.5,
            "oxigeno_mg_l": 8.1,
            "ph": 7.3,
            "medido_en": "2026-10-22T08:00:00Z",
        },
        headers=como_operario,
    )
    return eid


def _crear_clave(cliente, como_admin, nombre="ERP de prueba") -> dict:
    r = cliente.post("/api/integraciones", json={"nombre": nombre}, headers=como_admin)
    assert r.status_code == 201, r.text
    return r.json()


def test_cp_rf09_01_sistema_externo_consume_json(cliente, como_admin, estanque_id):
    """CP-RF09-01: con X-API-Key válida se obtienen estanques y lecturas en JSON."""
    clave = _crear_clave(cliente, como_admin)
    assert clave["clave"].startswith("ts_") and clave["prefijo"] == clave["clave"][:11]
    cab = {"X-API-Key": clave["clave"]}
    r = cliente.get("/api/externa/v1/estanques", headers=cab)
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/json")
    estado = next(e for e in r.json() if e["id"] == estanque_id)
    assert estado["ultima_lectura"]["oxigeno_mg_l"] == 8.1
    assert estado["niveles"]["OXIGENO_DISUELTO"] == "NORMAL"
    r = cliente.get(
        f"/api/externa/v1/estanques/{estanque_id}/lecturas?desde=2026-10-22&hasta=2026-10-22",
        headers=cab,
    )
    assert r.status_code == 200 and len(r.json()) == 1
    listado = cliente.get("/api/integraciones", headers=como_admin).json()
    assert listado[0]["ultimo_uso"] is not None and "clave" not in listado[0]


def test_cp_rf09_02_clave_invalida_o_revocada_da_401(cliente, como_admin, estanque_id):
    """CP-RF09-02: sin clave, con clave falsa o revocada -> 401 y sin datos."""
    assert cliente.get("/api/externa/v1/estanques").status_code == 401
    r = cliente.get("/api/externa/v1/estanques", headers={"X-API-Key": "ts_falsa"})
    assert r.status_code == 401 and r.json()["error"] == "clave_invalida"
    clave = _crear_clave(cliente, como_admin)
    assert (
        cliente.delete(f"/api/integraciones/{clave['id']}", headers=como_admin).json()["activa"]
        is False
    )
    r = cliente.get("/api/externa/v1/estanques", headers={"X-API-Key": clave["clave"]})
    assert r.status_code == 401


def test_jwt_de_usuario_no_sirve_para_la_api_externa(cliente, como_admin):
    assert cliente.get("/api/externa/v1/estanques", headers=como_admin).status_code == 401


def test_solo_admin_emite_claves(cliente, como_piscicultor):
    r = cliente.post("/api/integraciones", json={"nombre": "X sistema"}, headers=como_piscicultor)
    assert r.status_code == 403


def test_web_integraciones(cliente):
    cliente.post("/login", data={"nombre_usuario": "admin", "password": "Admin123!"})
    r = cliente.post("/integraciones", data={"nombre": "ERP web"})
    assert r.status_code == 200 and "no se volverá a mostrar" in r.text and "ts_" in r.text
    clave_id = cliente.get("/api/integraciones").json()[0]["id"]
    r = cliente.post(f"/integraciones/{clave_id}/revocar")
    assert "revocada" in r.text and "Revocada" in r.text
    assert cliente.post("/integraciones", data={"nombre": "x"}).status_code == 422
