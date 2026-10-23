"""Pruebas de tools/gqm_metrics.py: las métricas salen de artefactos y no se inventan."""

from pathlib import Path

import pytest

from tools import gqm_metrics as g

COVERAGE = """<?xml version="1.0" ?>
<coverage>
  <sources><source>{fuente}</source></sources>
  <packages><package name="x"><classes>
    <class filename="errores.py"><lines><line number="1" hits="1"/><line number="2" hits="0"/></lines></class>
    <class filename="model/a.py"><lines><line number="1" hits="3"/><line number="2" hits="1"/></lines></class>
  </classes></package></packages>
</coverage>
"""


@pytest.fixture
def raiz(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(g, "RAIZ", tmp_path)
    (tmp_path / "docs" / "gqm").mkdir(parents=True)
    return tmp_path


def test_m2_3_cuenta_todos_los_archivos_del_dominio(raiz: Path):
    (raiz / "coverage.xml").write_text(
        COVERAGE.format(fuente="D:\\repo\\src\\domain"), encoding="utf-8"
    )
    m = g.m2_3()
    assert m.valor == 75.0 and "3 de 4" in m.detalle


def test_m2_3_ignora_archivos_fuera_del_dominio(raiz: Path):
    (raiz / "coverage.xml").write_text(
        COVERAGE.format(fuente="/repo/src/adapters"), encoding="utf-8"
    )
    assert g.m2_3().valor is None


def test_m2_3_sin_coverage_es_pendiente(raiz: Path):
    m = g.m2_3()
    assert m.valor is None and m.texto_valor() == "pendiente"
    assert g.evaluar_meta(m, 1)[1] == "⏳ pendiente"


def _indicadores(raiz: Path, as_is, to_be) -> None:
    (raiz / "docs" / "gqm" / "valor_indicadores.yaml").write_text(
        f"""indicadores:
  - {{id: IV-1, nombre: a, unidad: min, sentido: menor_es_mejor, as_is: {as_is}, to_be_inc1: {to_be}}}
  - {{id: IV-2, nombre: b, unidad: h, sentido: menor_es_mejor, as_is: 10, to_be_inc1: 5}}
  - {{id: IV-3, nombre: c, unidad: n, sentido: mayor_es_mejor, as_is: 2, to_be_inc1: 4}}
""",
        encoding="utf-8",
    )


def test_m3_2_pendiente_si_falta_linea_base(raiz: Path):
    _indicadores(raiz, "null", 30)
    m = g.m3_2(1)
    assert m.valor is None and "IV-1: pendiente" in m.detalle


def test_m3_2_promedia_mejoras(raiz: Path):
    _indicadores(raiz, 600, 30)  # (600-30)/600 = 95 %, 50 %, 100 %
    m = g.m3_2(1)
    assert m.valor == pytest.approx((95 + 50 + 100) / 3)


def test_m2_2_lee_defectos_csv_si_no_hay_gh(raiz: Path, monkeypatch):
    monkeypatch.setattr(g, "_bugs_gh", lambda inc: None)
    (raiz / "docs" / "gqm" / "defectos.csv").write_text(
        "id,incremento,rf,titulo,estado,issue\nD1,1,RF-04,x,cerrado,\nD2,2,RF-05,y,abierto,\n",
        encoding="utf-8",
    )
    m = g.m2_2(1)
    assert m.valor == 0.25 and "defectos.csv" in m.detalle


def test_evaluar_meta():
    assert g.evaluar_meta(g.Metrica("M2.2", "x", 0.5, "{:.2f}", ""), 2)[1] == "❌ no cumple"
    assert g.evaluar_meta(g.Metrica("M3.1", "x", 90.0, "{:.0f} %", ""), 2)[1] == "✅ cumple"
