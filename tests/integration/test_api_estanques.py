"""RF-02 por la API REST y la web sobre SQLite."""

import pytest

LOTE = {"codigo": "L-100", "num_peces": 5000, "peso_medio_g": 12.5, "fecha_siembra": "2026-10-01"}


@pytest.fixture
def estanque_id(cliente, como_piscicultor) -> int:
    r = cliente.post(
        "/api/estanques",
        json={"nombre": "Estanque B1", "tipo": "ESTANQUE", "volumen_m3": 100, "ubicacion": "Sur"},
        headers=como_piscicultor,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_cp_rf02_01_crear_estanque_y_lote_aparece_en_listado(
    cliente, como_piscicultor, como_operario, estanque_id
):
    """CP-RF02-01: estanque con lote activo visible en el listado."""
    r = cliente.post(f"/api/estanques/{estanque_id}/lotes", json=LOTE, headers=como_piscicultor)
    assert r.status_code == 201 and r.json()["activo"] is True
    listado = cliente.get("/api/estanques", headers=como_operario).json()
    assert listado[0]["nombre"] == "Estanque B1"
    assert listado[0]["lote_activo"]["codigo"] == "L-100"
    assert listado[0]["lote_activo"]["num_peces_inicial"] == 5000


@pytest.mark.parametrize(
    ("cambio", "campo"),
    [({"num_peces": 0}, "num_peces"), ({"peso_medio_g": -1}, "peso_medio_g")],
)
def test_cp_rf02_02_lote_invalido_da_422_y_no_guarda(
    cliente, como_piscicultor, estanque_id, cambio, campo
):
    """CP-RF02-02: peces <= 0 o peso <= 0 -> 422 indicando el campo; nada se guarda."""
    r = cliente.post(
        f"/api/estanques/{estanque_id}/lotes", json={**LOTE, **cambio}, headers=como_piscicultor
    )
    assert r.status_code == 422
    assert r.json()["error"] == "validacion" and r.json()["campo"] == campo
    lotes = cliente.get(f"/api/estanques/{estanque_id}/lotes", headers=como_piscicultor).json()
    assert lotes == []


def test_segundo_lote_activo_da_409(cliente, como_piscicultor, estanque_id):
    url = f"/api/estanques/{estanque_id}/lotes"
    assert cliente.post(url, json=LOTE, headers=como_piscicultor).status_code == 201
    r = cliente.post(url, json={**LOTE, "codigo": "L-101"}, headers=como_piscicultor)
    assert r.status_code == 409 and "ya tiene el lote activo" in r.json()["detalle"]


def test_ciclo_completo_de_lote(cliente, como_piscicultor, estanque_id):
    lote = cliente.post(
        f"/api/estanques/{estanque_id}/lotes", json=LOTE, headers=como_piscicultor
    ).json()
    r = cliente.put(
        f"/api/lotes/{lote['id']}/peso", json={"peso_medio_g": 20}, headers=como_piscicultor
    )
    assert r.status_code == 200 and r.json()["peso_medio_actual_g"] == 20
    r = cliente.post(
        f"/api/lotes/{lote['id']}/cerrar",
        json={"fecha_cierre": "2026-10-20"},
        headers=como_piscicultor,
    )
    assert r.status_code == 200 and r.json()["activo"] is False
    assert (
        cliente.get(f"/api/lotes/{lote['id']}", headers=como_piscicultor).json()["fecha_cierre"]
        == "2026-10-20"
    )
    assert (
        cliente.delete(f"/api/estanques/{estanque_id}", headers=como_piscicultor).status_code == 204
    )
    assert cliente.get("/api/estanques", headers=como_piscicultor).json() == []


def test_actualizar_y_obtener_estanque(cliente, como_piscicultor, estanque_id):
    r = cliente.put(
        f"/api/estanques/{estanque_id}",
        json={"nombre": "B1 grande", "tipo": "JAULA"},
        headers=como_piscicultor,
    )
    assert r.status_code == 200 and r.json()["tipo"] == "JAULA"
    assert (
        cliente.get(f"/api/estanques/{estanque_id}", headers=como_piscicultor).json()["nombre"]
        == "B1 grande"
    )


def test_operario_no_puede_crear_estanques(cliente, como_operario):
    r = cliente.post("/api/estanques", json={"nombre": "X"}, headers=como_operario)
    assert r.status_code == 403


def test_estanque_inexistente_da_404(cliente, como_operario):
    r = cliente.get("/api/estanques/999", headers=como_operario)
    assert r.status_code == 404 and r.json()["error"] == "no_encontrado"


def test_web_crear_estanque_y_sembrar_lote(cliente):
    cliente.post("/login", data={"nombre_usuario": "piscicultor", "password": "Pisci123!"})
    r = cliente.post(
        "/estanques", data={"nombre": "Jaula W", "tipo": "JAULA", "volumen_m3": "80,5"}
    )
    assert r.status_code == 200 and "Jaula W" in r.text
    estanque_id = cliente.get("/api/estanques").json()[0]["id"]
    r = cliente.post(
        f"/estanques/{estanque_id}/lotes",
        data={
            "codigo": "L-W",
            "num_peces": "0",
            "peso_medio_g": "10",
            "fecha_siembra": "2026-10-01",
        },
    )
    assert r.status_code == 422 and "número de peces debe ser mayor que 0" in r.text
    r = cliente.post(
        f"/estanques/{estanque_id}/lotes",
        data={
            "codigo": "L-W",
            "num_peces": "300",
            "peso_medio_g": "abc",
            "fecha_siembra": "2026-10-01",
        },
    )
    assert r.status_code == 422 and "peso_medio_g debe ser numérico" in r.text
    r = cliente.post(
        f"/estanques/{estanque_id}/lotes",
        data={
            "codigo": "L-W",
            "num_peces": "300",
            "peso_medio_g": "10",
            "fecha_siembra": "2026-10-01",
        },
    )
    assert r.status_code == 200 and "Lote L-W sembrado" in r.text
    lote_id = cliente.get(f"/api/estanques/{estanque_id}").json()["lote_activo"]["id"]
    assert (
        "Peso medio actualizado"
        in cliente.post(f"/lotes/{lote_id}/peso", data={"peso_medio_g": "15"}).text
    )
    r = cliente.post(f"/estanques/{estanque_id}/baja")
    assert r.status_code == 409 and "lote activo" in r.text
    assert (
        "cerrado"
        in cliente.post(f"/lotes/{lote_id}/cerrar", data={"fecha_cierre": "2026-10-22"}).text
    )
    r = cliente.post(f"/estanques/{estanque_id}", data={"nombre": "Jaula W2", "tipo": "JAULA"})
    assert "Cambios guardados" in r.text
    assert "dado de baja" in cliente.post(f"/estanques/{estanque_id}/baja").text
    panel = cliente.get("/panel")
    assert panel.status_code == 200 and "Jaula W2" not in panel.text
