"""RF-04 por la API REST y la web sobre SQLite."""

import time
from pathlib import Path

import pytest

from src.adapters.config import RAIZ, cargar_umbrales
from src.domain.errores import ErrorValidacion
from tests.umbrales import UMBRALES


@pytest.fixture
def estanque_id(cliente, como_piscicultor) -> int:
    r = cliente.post("/api/estanques", json={"nombre": "E-alertas"}, headers=como_piscicultor)
    return r.json()["id"]


def _lectura(cliente, enc, estanque_id, od=8.0, t=12.0, ph=7.2):
    r = cliente.post(
        "/api/lecturas",
        json={"estanque_id": estanque_id, "temperatura_c": t, "oxigeno_mg_l": od, "ph": ph},
        headers=enc,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_config_umbrales_yaml_coincide_con_valores_de_referencia():
    assert cargar_umbrales(RAIZ / "config" / "umbrales.yaml") == UMBRALES


def test_config_umbrales_invalida_falla_al_cargar(tmp_path: Path):
    malo = tmp_path / "u.yaml"
    malo.write_text(
        (RAIZ / "config" / "umbrales.yaml")
        .read_text(encoding="utf-8")
        .replace("precaucion: [6.0, 9.0]", "precaucion: [7.0, 8.0]"),
        encoding="utf-8",
    )
    with pytest.raises(ErrorValidacion, match="debe contener"):
        cargar_umbrales(malo)


def test_cp_rf04_01_od_critico_crea_alerta_visible_en_panel_en_menos_de_2s(
    cliente, como_operario, estanque_id
):
    """CP-RF04-01: OD 4.5 -> alerta CRÍTICA en la respuesta y en el panel en < 2 s."""
    inicio = time.perf_counter()
    cuerpo = _lectura(cliente, como_operario, estanque_id, od=4.5)
    panel = cliente.get("/api/panel", headers=como_operario).json()
    assert time.perf_counter() - inicio < 2.0
    (alerta,) = cuerpo["alertas"]
    assert alerta["nivel"] == "CRITICA" and alerta["parametro"] == "OXIGENO_DISUELTO"
    assert {e["parametro"]: e["nivel"] for e in cuerpo["evaluacion"]} == {
        "TEMPERATURA": "NORMAL",
        "OXIGENO_DISUELTO": "CRITICA",
        "PH": "NORMAL",
    }
    estado = next(e for e in panel if e["estanque_id"] == estanque_id)
    assert [a["id"] for a in estado["alertas_abiertas"]] == [alerta["id"]]
    assert estado["niveles"]["OXIGENO_DISUELTO"] == "CRITICA"


@pytest.mark.parametrize(("od", "nivel"), [(6.0, "PRECAUCION"), (7.0, None)])
def test_cp_rf04_01_precaucion_y_normal(cliente, como_operario, estanque_id, od, nivel):
    """CP-RF04-01: OD 6 -> PRECAUCIÓN; OD 7 -> sin alerta."""
    alertas = _lectura(cliente, como_operario, estanque_id, od=od)["alertas"]
    assert [a["nivel"] for a in alertas] == ([nivel] if nivel else [])


def test_cp_rf04_02_sin_duplicados_y_atencion_con_usuario_y_hora(
    cliente, como_operario, estanque_id, reloj
):
    """CP-RF04-02: no se duplica la alerta abierta; atenderla registra usuario y fecha/hora."""
    alerta = _lectura(cliente, como_operario, estanque_id, od=4.5)["alertas"][0]
    assert _lectura(cliente, como_operario, estanque_id, od=4.4)["alertas"] == []
    abiertas = cliente.get(
        f"/api/alertas?estado=ABIERTA&estanque_id={estanque_id}", headers=como_operario
    ).json()
    assert len(abiertas) == 1

    yo = cliente.get("/api/auth/yo", headers=como_operario).json()
    r = cliente.post(
        f"/api/alertas/{alerta['id']}/atender",
        json={"observacion": "Aireador encendido"},
        headers=como_operario,
    )
    assert r.status_code == 200
    atendida = r.json()
    assert atendida["estado"] == "ATENDIDA" and atendida["atendida_por"] == yo["id"]
    assert atendida["atendida_en"].startswith(reloj.ahora().strftime("%Y-%m-%dT%H:%M"))
    assert atendida["observacion"] == "Aireador encendido"
    r = cliente.post(f"/api/alertas/{alerta['id']}/atender", headers=como_operario)
    assert r.status_code == 409


def test_atender_alerta_inexistente_da_404(cliente, como_operario):
    assert cliente.post("/api/alertas/999/atender", headers=como_operario).status_code == 404


def test_web_panel_y_pagina_de_alertas(cliente, estanque_id):
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    r = cliente.post(
        "/lecturas",
        data={"estanque_id": estanque_id, "temperatura_c": "19", "oxigeno_mg_l": "8", "ph": "7"},
    )
    assert "1 alerta(s) generada(s)" in r.text and "nivel-CRITICA" in r.text
    pagina = cliente.get("/alertas")
    assert "Temperatura en CRÍTICA: 19.00 °C" in pagina.text
    alerta_id = cliente.get("/api/alertas?estado=ABIERTA").json()[0]["id"]
    r = cliente.post(f"/alertas/{alerta_id}/atender", data={"observacion": "Sombra instalada"})
    assert f"Alerta {alerta_id} atendida" in r.text
    assert "Usuario Operario" in r.text and "Sombra instalada" in r.text
    r = cliente.post(f"/alertas/{alerta_id}/atender", data={"observacion": ""})
    assert r.status_code == 409 and "ya fue atendida" in r.text
