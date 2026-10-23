"""RF-08 por la API REST, la web y el generador real (csv + reportlab)."""

import csv
import io
import time

import pytest


@pytest.fixture
def datos(cliente, como_piscicultor, como_operario):
    eid = cliente.post(
        "/api/estanques", json={"nombre": "E-reportes"}, headers=como_piscicultor
    ).json()["id"]
    lote = cliente.post(
        f"/api/estanques/{eid}/lotes",
        json={
            "codigo": "L-REP",
            "num_peces": 1000,
            "peso_medio_g": 50,
            "fecha_siembra": "2026-09-01",
        },
        headers=como_piscicultor,
    ).json()
    for medido_en, od in (("2026-10-15T08:00:00Z", 8.0), ("2026-10-16T08:00:00Z", 4.5),
                          ("2026-10-21T08:00:00Z", 7.5)):  # fmt: skip
        cliente.post(
            "/api/lecturas",
            json={"estanque_id": eid, "temperatura_c": 12.5, "oxigeno_mg_l": od, "ph": 7.3,
                  "medido_en": medido_en},
            headers=como_operario,
        )  # fmt: skip
    cliente.post(
        f"/api/lotes/{lote['id']}/alimentacion",
        json={"cantidad_kg": 35.04, "registrado_en": "2026-10-16T09:00:00Z"},
        headers=como_operario,
    )
    cliente.post(
        f"/api/lotes/{lote['id']}/mortalidad",
        json={"cantidad": 10, "registrado_en": "2026-10-16T10:00:00Z"},
        headers=como_operario,
    )
    cliente.put(
        f"/api/lotes/{lote['id']}/peso", json={"peso_medio_g": 80}, headers=como_piscicultor
    )
    return eid


def _descargar(cliente, enc, ruta):
    inicio = time.perf_counter()
    r = cliente.get(ruta, headers=enc)
    return r, time.perf_counter() - inicio


def test_cp_rf08_01_csv_calidad_agua_en_menos_de_5s(cliente, como_piscicultor, datos):
    """CP-RF08-01: CSV con encabezados y solo las filas del rango, descargado en < 5 s."""
    r, segundos = _descargar(
        cliente,
        como_piscicultor,
        "/api/reportes/calidad-agua.csv?desde=2026-10-15&hasta=2026-10-20",
    )
    assert r.status_code == 200 and segundos < 5
    assert r.headers["content-type"].startswith("text/csv")
    assert (
        'filename="truchasmart_calidad-agua_2026-10-15_2026-10-20.csv"'
        in r.headers["content-disposition"]
    )
    filas = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert [f["oxigeno_mg_l"] for f in filas] == ["8.00", "4.50"]
    assert filas[1]["nivel_oxigeno"] == "CRITICA" and filas[1]["estanque"] == "E-reportes"


def test_cp_rf08_01_csv_produccion(cliente, como_piscicultor, datos):
    """CP-RF08-01: CSV de producción con biomasa y FCR del lote."""
    r = cliente.get(
        "/api/reportes/produccion.csv?desde=2026-10-01&hasta=2026-10-31", headers=como_piscicultor
    )
    (fila,) = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert (fila["lote"], fila["peces_vivos"], fila["biomasa_kg"], fila["fcr"]) == (
        "L-REP", "990", "79.200", "1.20",
    )  # fmt: skip
    assert fila["alimento_periodo_kg"] == "35.040" and fila["mortalidad_periodo"] == "10"


@pytest.mark.parametrize("tipo", ["calidad-agua", "produccion"])
def test_cp_rf08_02_pdf_valido_en_menos_de_5s(cliente, como_piscicultor, datos, tipo):
    """CP-RF08-02: PDF válido (%PDF) descargado en < 5 s."""
    r, segundos = _descargar(
        cliente, como_piscicultor, f"/api/reportes/{tipo}.pdf?desde=2026-10-01&hasta=2026-10-31"
    )
    assert r.status_code == 200 and segundos < 5
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF") and r.content.rstrip().endswith(b"%%EOF")
    assert len(r.content) > 1500


def test_cp_rf08_02_rango_invertido_da_422(cliente, como_piscicultor):
    """CP-RF08-02: fecha inicio > fecha fin -> 422."""
    r = cliente.get(
        "/api/reportes/produccion.pdf?desde=2026-10-20&hasta=2026-10-01", headers=como_piscicultor
    )
    assert r.status_code == 422 and r.json()["campo"] == "desde"


def test_formato_o_tipo_desconocido_y_permisos(cliente, como_piscicultor, como_operario):
    r = cliente.get(
        "/api/reportes/ventas.csv?desde=2026-10-01&hasta=2026-10-02", headers=como_piscicultor
    )
    assert r.status_code == 422
    r = cliente.get(
        "/api/reportes/produccion.xlsx?desde=2026-10-01&hasta=2026-10-02", headers=como_piscicultor
    )
    assert r.status_code == 422
    r = cliente.get(
        "/api/reportes/produccion.csv?desde=2026-10-01&hasta=2026-10-02", headers=como_operario
    )
    assert r.status_code == 403


def test_pdf_largo_se_trunca_con_aviso(cliente, como_piscicultor, recursos):
    from datetime import UTC, date, datetime, timedelta

    from src.domain.model.lectura_agua import Parametro
    from src.domain.model.umbral import Nivel
    from src.ports.inbound.exportar_reporte import FilaCalidad, Reporte, TipoReporte

    niveles = dict.fromkeys(Parametro, Nivel.NORMAL)
    filas = [
        FilaCalidad(
            "A",
            datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i),
            12,
            8,
            7,
            "SENSOR",
            niveles,
        )
        for i in range(1600)
    ]
    reporte = Reporte(TipoReporte.CALIDAD_AGUA, "R", date(2026, 1, 1), date(2026, 1, 2),
                      datetime(2026, 1, 3, tzinfo=UTC), "X", filas, [], [])  # fmt: skip
    inicio = time.perf_counter()
    pdf = recursos.generador_reportes.pdf(reporte)
    assert pdf.startswith(b"%PDF") and time.perf_counter() - inicio < 5
    assert len(recursos.generador_reportes.csv(reporte).decode("utf-8-sig").splitlines()) == 1601


def test_web_reportes(cliente, datos):
    cliente.post("/login", data={"nombre_usuario": "piscicultor", "password": "Pisci123!"})
    assert "Exportar reporte" in cliente.get("/reportes").text
    r = cliente.get("/reportes/vista?tipo=produccion&desde=2026-10-01&hasta=2026-10-31")
    assert r.status_code == 200 and "L-REP" in r.text and "1.20" in r.text
    assert (
        "/reportes/descargar?tipo=produccion&amp;desde=2026-10-01&amp;hasta=2026-10-31&amp;formato=pdf"
        in r.text
    )
    r = cliente.get("/reportes/vista?tipo=calidad-agua&desde=2026-10-15&hasta=2026-10-20")
    assert "E-reportes" in r.text and "<strong>2</strong> lecturas" in r.text
    assert (
        cliente.get("/reportes/vista?tipo=produccion&desde=x&hasta=2026-10-31").status_code == 422
    )
    r = cliente.get(
        "/reportes/descargar?tipo=produccion&formato=pdf&desde=2026-10-01&hasta=2026-10-31"
    )
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    r = cliente.get(
        "/reportes/descargar?tipo=produccion&formato=csv&desde=2026-10-31&hasta=2026-10-01"
    )
    assert r.status_code == 422 and "posterior" in r.text
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    assert cliente.get("/reportes").status_code == 403
