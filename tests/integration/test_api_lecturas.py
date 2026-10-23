"""RF-03 por la API REST, la web y el simulador sobre SQLite."""

import argparse
import time

import pytest

from src.adapters.inbound.simulator.__main__ import crear_parser, ejecutar
from src.adapters.inbound.simulator.escenarios import generar

LECTURA = {"temperatura_c": 12.6, "oxigeno_mg_l": 8.1, "ph": 7.4}


@pytest.fixture
def estanque_id(cliente, como_piscicultor) -> int:
    r = cliente.post("/api/estanques", json={"nombre": "E-lecturas"}, headers=como_piscicultor)
    return r.json()["id"]


def test_cp_rf03_01_post_lectura_y_visible_en_panel_en_menos_de_2s(
    cliente, como_operario, estanque_id
):
    """CP-RF03-01: lectura válida vía API, guardada con usuario y visible en el panel < 2 s."""
    inicio = time.perf_counter()
    r = cliente.post(
        "/api/lecturas", json={"estanque_id": estanque_id, **LECTURA}, headers=como_operario
    )
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["fuente"] == "SENSOR" and cuerpo["registrado_por"] is not None
    panel = cliente.get("/api/panel", headers=como_operario).json()
    transcurrido = time.perf_counter() - inicio
    estado = next(e for e in panel if e["estanque_id"] == estanque_id)
    assert estado["ultima_lectura"]["id"] == cuerpo["id"]
    assert transcurrido < 2.0
    ultima = cliente.get(f"/api/estanques/{estanque_id}/ultima-lectura", headers=como_operario)
    assert ultima.json()["oxigeno_mg_l"] == 8.1


@pytest.mark.parametrize(
    ("cambio", "campo"),
    [
        ({"ph": 14.5}, "ph"),
        ({"ph": -1}, "ph"),
        ({"oxigeno_mg_l": -0.2}, "oxigeno_mg_l"),
        ({"temperatura_c": 41}, "temperatura_c"),
        ({"temperatura_c": -3}, "temperatura_c"),
    ],
)
def test_cp_rf03_02_valores_imposibles_dan_422(cliente, como_operario, estanque_id, cambio, campo):
    """CP-RF03-02: valores físicamente imposibles -> 422 indicando el parámetro."""
    r = cliente.post(
        "/api/lecturas",
        json={"estanque_id": estanque_id, **LECTURA, **cambio},
        headers=como_operario,
    )
    assert r.status_code == 422
    assert r.json()["campo"] == campo and "físicamente imposible" in r.json()["detalle"]
    assert (
        cliente.get(f"/api/lecturas?estanque_id={estanque_id}", headers=como_operario).json() == []
    )


def test_lectura_requiere_autenticacion_y_estanque_existente(cliente, como_operario):
    assert cliente.post("/api/lecturas", json={"estanque_id": 1, **LECTURA}).status_code == 401
    r = cliente.post("/api/lecturas", json={"estanque_id": 999, **LECTURA}, headers=como_operario)
    assert r.status_code == 404


def test_listado_de_lecturas_ordenado(cliente, como_operario, estanque_id):
    for od in (8.0, 7.5, 7.2):
        cliente.post(
            "/api/lecturas",
            json={
                "estanque_id": estanque_id,
                **LECTURA,
                "oxigeno_mg_l": od,
                "medido_en": f"2026-10-23T0{int(od * 10) % 10}:00:00Z",
            },
            headers=como_operario,
        )
    datos = cliente.get(
        f"/api/lecturas?estanque_id={estanque_id}&limite=2", headers=como_operario
    ).json()
    assert [d["oxigeno_mg_l"] for d in datos] == [7.5, 7.2]


def test_web_formulario_de_lectura(cliente, estanque_id):
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    assert "E-lecturas" in cliente.get(f"/lecturas/nueva?estanque_id={estanque_id}").text
    r = cliente.post(
        "/lecturas",
        data={"estanque_id": estanque_id, "temperatura_c": "13,1", "oxigeno_mg_l": "8", "ph": "16"},
    )
    assert r.status_code == 422 and "El pH 16 es físicamente imposible" in r.text
    r = cliente.post(
        "/lecturas",
        data={
            "estanque_id": estanque_id,
            "temperatura_c": "13,1",
            "oxigeno_mg_l": "8",
            "ph": "7.5",
        },
    )
    assert r.status_code == 200 and "Lectura registrada" in r.text and "13.10" in r.text
    ultima = cliente.get(f"/api/estanques/{estanque_id}/ultima-lectura").json()
    assert ultima["fuente"] == "MANUAL" and ultima["temperatura_c"] == 13.1


def test_simulador_envia_lecturas_a_la_api(cliente, estanque_id, como_operario):
    args = crear_parser().parse_args(
        [
            "--estanque",
            str(estanque_id),
            "--escenario",
            "critico_oxigeno",
            "--intervalo",
            "0",
            "--cantidad",
            "4",
            "--semilla",
            "1",
        ]
    )
    esperas = []
    assert ejecutar(args, cliente, dormir=esperas.append) == 4
    assert esperas == [0, 0, 0]
    lecturas = cliente.get(f"/api/lecturas?estanque_id={estanque_id}", headers=como_operario).json()
    assert [x["oxigeno_mg_l"] for x in lecturas] == [6.8, 7.2, 7.6, 8.0]
    assert {x["fuente"] for x in lecturas} == {"SENSOR"}


def test_simulador_con_credenciales_invalidas(cliente, estanque_id, capsys):
    args = argparse.Namespace(
        usuario="operario",
        password="mala",
        escenario="normal",
        semilla=None,
        estanque=estanque_id,
        cantidad=1,
        intervalo=0,
        url="test",
    )
    assert ejecutar(args, cliente) == 0
    assert "Error de autenticación (401)" in capsys.readouterr().err


@pytest.mark.parametrize("escenario", ["normal", "critico_oxigeno", "critico_temperatura"])
def test_escenarios_generan_valores_fisicamente_validos(escenario):
    valores = [m for _, m in zip(range(30), generar(escenario, semilla=3), strict=False)]
    assert all(
        0 <= m.temperatura_c <= 40 and m.oxigeno_mg_l >= 0 and 0 <= m.ph <= 14 for m in valores
    )
    if escenario == "critico_oxigeno":
        assert valores[-1].oxigeno_mg_l == 3.5
    if escenario == "critico_temperatura":
        assert valores[-1].temperatura_c == 20.0
    if escenario == "normal":
        assert all(10 <= m.temperatura_c <= 16 and m.oxigeno_mg_l >= 7 for m in valores)


def test_escenario_desconocido():
    with pytest.raises(ValueError):
        next(generar("tsunami"))
