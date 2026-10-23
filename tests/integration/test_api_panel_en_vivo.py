"""Interfaz en vivo (Issue #23): tendencia en /api/panel y sensor simulado controlado por API."""

import time

import pytest


@pytest.fixture
def estanque_id(cliente, como_piscicultor) -> int:
    return cliente.post(
        "/api/estanques", json={"nombre": "E-en-vivo"}, headers=como_piscicultor
    ).json()["id"]


def _esperar(condicion, segundos=5.0):
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if condicion():
            return True
        time.sleep(0.1)
    return False


def test_panel_incluye_tendencia_cronologica(cliente, como_operario, estanque_id):
    for i, od in enumerate((8.0, 7.5, 7.1)):
        cliente.post(
            "/api/lecturas",
            json={
                "estanque_id": estanque_id,
                "temperatura_c": 12,
                "oxigeno_mg_l": od,
                "ph": 7.2,
                "medido_en": f"2026-10-2{i}T08:00:00Z",
            },
            headers=como_operario,
        )
    panel = cliente.get("/api/panel?puntos=2", headers=como_operario).json()
    estado = next(e for e in panel if e["estanque_id"] == estanque_id)
    assert [p["oxigeno_mg_l"] for p in estado["tendencia"]] == [7.5, 7.1]
    assert estado["simulacion"] is None
    sin = cliente.get("/api/panel?puntos=0", headers=como_operario).json()
    assert next(e for e in sin if e["estanque_id"] == estanque_id)["tendencia"] == []


def test_iniciar_y_detener_sensor_simulado(cliente, como_piscicultor, como_operario, estanque_id):
    r = cliente.post(
        "/api/simulador",
        json={"estanque_id": estanque_id, "escenario": "critico_oxigeno", "intervalo_s": 60},
        headers=como_piscicultor,
    )
    assert r.status_code == 201 and r.json()["escenario"] == "critico_oxigeno"

    def hay_lectura():
        datos = cliente.get(f"/api/lecturas?estanque_id={estanque_id}", headers=como_operario)
        return len(datos.json()) >= 1

    estado = cliente.app.state.simulador._simulaciones.get(estanque_id)
    assert _esperar(hay_lectura), (
        f"el simulador no registró lecturas: activa={estado.activa}, "
        f"error={estado.ultimo_error!r}, enviadas={estado.lecturas_enviadas}"
    )
    lectura = cliente.get(f"/api/lecturas?estanque_id={estanque_id}", headers=como_operario).json()
    assert lectura[0]["fuente"] == "SENSOR" and lectura[0]["oxigeno_mg_l"] == 8.0
    panel = cliente.get("/api/panel", headers=como_operario).json()
    assert next(e for e in panel if e["estanque_id"] == estanque_id)["simulacion"] == (
        "critico_oxigeno"
    )
    activas = cliente.get("/api/simulador", headers=como_operario).json()
    assert [s["estanque_id"] for s in activas] == [estanque_id]

    assert (
        cliente.delete(f"/api/simulador/{estanque_id}", headers=como_piscicultor).status_code == 204
    )
    assert cliente.get("/api/simulador", headers=como_operario).json() == []
    assert (
        cliente.delete(f"/api/simulador/{estanque_id}", headers=como_piscicultor).status_code == 404
    )


def test_simulador_valida_permisos_y_datos(cliente, como_piscicultor, como_operario, estanque_id):
    cuerpo = {"estanque_id": estanque_id, "escenario": "normal", "intervalo_s": 5}
    assert cliente.post("/api/simulador", json=cuerpo, headers=como_operario).status_code == 403
    r = cliente.post(
        "/api/simulador", json={**cuerpo, "escenario": "tsunami"}, headers=como_piscicultor
    )
    assert r.status_code == 422 and r.json()["campo"] == "escenario"
    r = cliente.post("/api/simulador", json={**cuerpo, "intervalo_s": 0}, headers=como_piscicultor)
    assert r.status_code == 422 and r.json()["campo"] == "intervalo_s"
    r = cliente.post(
        "/api/simulador", json={**cuerpo, "estanque_id": 999}, headers=como_piscicultor
    )
    assert r.status_code == 404


def test_web_panel_y_paginas_en_vivo(cliente, estanque_id):
    cliente.post("/login", data={"nombre_usuario": "piscicultor", "password": "Pisci123!"})
    panel = cliente.get("/panel").text
    assert "canvas" in panel and "sim-boton" in panel and "/static/panel.js?v=" in panel
    assert "/static/vivo.js?v=" in panel
    assert 'id="contador-abiertas"' in cliente.get("/alertas").text
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    assert "sim-boton" not in cliente.get("/panel").text
