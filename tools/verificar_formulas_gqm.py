"""Verifica, con datos reales, que cada métrica GQM aplica la fórmula de la Matriz 3.1.

Para cada métrica recalcula de forma independiente el numerador y el denominador desde la fuente
de datos indicada en la matriz, muestra la operación, la compara con la meta de cada incremento
y comprueba que el valor coincide con el que reporta tools/gqm_metrics.py.

  Incremento 1 -> checkout del tag v1.0-PMV (--inc1)
  Incremento 2 -> este repositorio (--inc2, por defecto)

Requisitos: coverage.xml generado en cada checkout
(pytest -m "not e2e" --cov=src/domain --cov-report=xml) y `gh` autenticado para M2.2.

Uso:  python tools/verificar_formulas_gqm.py --inc1 ../trucha-v1pmv [--metrica M2.2]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

import gqm_metrics as g  # noqa: E402
from check_domain_purity import analizar_paquete  # noqa: E402

# Fórmula y metas tal como figuran en la Matriz 3.1 del informe.
MATRIZ = {
    "M1.1": ("Índice de contaminación del dominio",
             "módulos de src/domain que importan fuera de la biblioteca estándar ÷ total de módulos de src/domain × 100",
             "tools/check_domain_purity.py (AST) + import-linter", "0.0 %", "0.0 %"),
    "M1.2": ("Cohesión de módulos hexagonales",
             "componentes presentes y conformes (domain/model, domain/service, ports/inbound, ports/outbound, adapters) ÷ 5 × 100",
             "estructura del repositorio + contratos import-linter", "100 %", "100 %"),
    "M2.1": ("Cobertura funcional con capturas",
             "capturas existentes ÷ capturas esperadas (2 por RF) × 100",
             "evidencias/incN/RF0X_paso{1,2}_*.png", "100 %", "100 %"),
    "M2.2": ("Tasa de defectos funcionales",
             "n.º de Issues con labels bug + incN ÷ RF del incremento",
             "GitHub Issues", "≤ 1.0 Def/RF", "≤ 0.2 Def/RF"),
    "M2.3": ("Cobertura del dominio",
             "líneas ejecutadas ÷ líneas ejecutables de src/domain × 100",
             "coverage.xml de pytest-cov", "≥ 80 %", "≥ 80 %"),
    "M3.1": ("Cobertura de brechas resueltas",
             "brechas AS-IS resueltas y verificadas (capturas + pruebas CP del RF) ÷ 10 × 100",
             "docs/gqm/brechas.yaml", "≥ 60 %", "≥ 90 %"),
    "M3.2": ("Índice de impacto en valor",
             "promedio de la mejora % de IV-1, IV-2, IV-3 respecto del AS-IS (acotada a 100 %)",
             "docs/gqm/valor_indicadores.yaml + mediciones", "mejora ≥ 50 %", "mejora ≥ 80 %"),
}  # fmt: skip


def _cumple(valor: float | None, inc: int, metrica: str) -> bool | None:
    if valor is None:
        return None
    op, meta = g.METAS[metrica][inc]
    return valor <= meta if op == "<=" else valor >= meta


# ------------------------------------------------------------------ cálculo independiente


def calc_m1_1(raiz: Path, inc: int) -> tuple[str, str, float]:
    dom = analizar_paquete(raiz, "src.domain")
    num, den = len(dom.contaminados), dom.total
    return f"{num} módulos contaminados", f"{den} módulos", num / den * 100


def calc_m1_2(raiz: Path, inc: int) -> tuple[str, str, float]:
    exe = shutil.which("lint-imports")
    r = subprocess.run([exe], cwd=raiz, capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})  # fmt: skip
    contratos_ok = r.returncode == 0
    contaminados = {
        m.ruta.resolve()
        for paq in ("src.domain", "src.ports")
        for m in analizar_paquete(raiz, paq).contaminados
    }
    conformes = 0
    for carpetas in g.COMPONENTES.values():
        modulos = [p for c in carpetas for p in (raiz / c).rglob("*.py") if p.name != "__init__.py"]
        presentes = all(any((raiz / c).rglob("*.py")) for c in carpetas) and bool(modulos)
        puros = not any(p.resolve() in contaminados for p in modulos)
        conformes += presentes and puros and contratos_ok
    estado = "KEPT" if contratos_ok else "BROKEN"
    return (
        f"{conformes} componentes conformes (contratos {estado})",
        "5 componentes",
        conformes / 5 * 100,
    )


def calc_m2_1(raiz: Path, inc: int) -> tuple[str, str, float]:
    esperadas = [
        raiz / "evidencias" / f"inc{inc}" / f"RF{rf:02d}_paso{n}_{s}.png"
        for rf in g.RF_POR_INCREMENTO[inc]
        for n, s in ((1, "entrada"), (2, "resultado"))
    ]
    existentes = sum(p.is_file() and p.stat().st_size > 0 for p in esperadas)
    return (
        f"{existentes} capturas existentes",
        f"{len(esperadas)} esperadas",
        existentes / len(esperadas) * 100,
    )


def calc_m2_2(raiz: Path, inc: int) -> tuple[str, str, float]:
    r = subprocess.run(
        ["gh", "issue", "list", "--state", "all", "--label", "bug", "--label", f"inc{inc}",
         "--json", "number"], cwd=raiz, capture_output=True, text=True, encoding="utf-8",
    )  # fmt: skip
    numeros = [i["number"] for i in json.loads(r.stdout or "[]")]
    rf = len(g.RF_POR_INCREMENTO[inc])
    ids = ", ".join(f"#{n}" for n in numeros) or "ninguno"
    return f"{len(numeros)} defecto(s): {ids}", f"{rf} RF", len(numeros) / rf


def calc_m2_3(raiz: Path, inc: int) -> tuple[str, str, float]:
    raiz_xml = ET.parse(raiz / "coverage.xml").getroot()
    cubiertas = total = 0
    for clase in raiz_xml.iter("class"):
        for linea in clase.iter("line"):
            total += 1
            cubiertas += int(linea.get("hits", "0")) > 0
    return f"{cubiertas} líneas ejecutadas", f"{total} líneas ejecutables", cubiertas / total * 100


def calc_m3_1(raiz: Path, inc: int) -> tuple[str, str, float]:
    datos = yaml.safe_load((raiz / "docs" / "gqm" / "brechas.yaml").read_text(encoding="utf-8"))
    pruebas = "\n".join(p.read_text(encoding="utf-8") for p in (raiz / "tests").rglob("*.py"))
    resueltas = []
    for b in datos["brechas"]:
        if b.get("resuelta_en") is None or b["resuelta_en"] > inc:
            continue
        ok = True
        for rf in b["rf"]:
            n = int(rf.split("-")[1])
            carpeta = raiz / "evidencias" / f"inc{1 if n <= 4 else 2}"
            ok &= all((carpeta / f"RF{n:02d}_paso{k}_{s}.png").is_file()
                      for k, s in ((1, "entrada"), (2, "resultado")))  # fmt: skip
            ok &= f"CP-RF{n:02d}-01" in pruebas.upper().replace("_", "-") and (
                f"CP-RF{n:02d}-02" in pruebas.upper().replace("_", "-")
            )
        if ok:
            resueltas.append(b["id"])
    total = len(datos["brechas"])
    return (
        f"{len(resueltas)} resueltas ({', '.join(resueltas)})",
        f"{total} brechas",
        len(resueltas) / total * 100,
    )


def calc_m3_2(raiz: Path, inc: int) -> tuple[str, str, float | None]:
    # Las mediciones de valor se registraron en main (PR #22): se usan para ambos incrementos.
    datos = yaml.safe_load(
        (RAIZ / "docs" / "gqm" / "valor_indicadores.yaml").read_text(encoding="utf-8")
    )
    mejoras, partes = [], []
    for iv in datos["indicadores"]:
        a, t = iv.get("as_is"), iv.get(f"to_be_inc{inc}")
        if a in (None, "") or t in (None, ""):
            partes.append(f"{iv['id']}: sin dato")
            continue
        a, t = float(a), float(t)
        m = (
            (a - t) / a * 100
            if iv["sentido"] == "menor_es_mejor"
            else min(100.0, (t - a) / a * 100)
        )
        mejoras.append(m)
        partes.append(f"{iv['id']} {m:.1f} % ({iv.get('as_is_tipo')})")
    valor = sum(mejoras) / len(mejoras) if mejoras else None
    return "; ".join(partes), f"{len(mejoras)} de {len(datos['indicadores'])} IV con dato", valor


CALCULOS = {
    "M1.1": (calc_m1_1, g.m1_1, "{:.1f} %"),
    "M1.2": (calc_m1_2, g.m1_2, "{:.0f} %"),
    "M2.1": (calc_m2_1, g.m2_1, "{:.0f} %"),
    "M2.2": (calc_m2_2, g.m2_2, "{:.2f} Def/RF"),
    "M2.3": (calc_m2_3, g.m2_3, "{:.1f} %"),
    "M3.1": (calc_m3_1, g.m3_1, "{:.0f} %"),
    "M3.2": (calc_m3_2, g.m3_2, "{:.1f} %"),
}


def valor_herramienta(metrica: str, raiz: Path, inc: int) -> tuple[float | None, str | None]:
    g.RAIZ = raiz if metrica != "M3.2" else RAIZ
    funcion = CALCULOS[metrica][1]
    m = funcion(inc) if metrica in ("M2.1", "M2.2", "M3.1", "M3.2") else funcion()
    return m.valor, m.advertencia


def verificar(metrica: str, raices: dict[int, Path]) -> bool:
    nombre, formula, fuente, meta1, meta2 = MATRIZ[metrica]
    calcular, _, formato = CALCULOS[metrica]
    print(f"{metrica} · {nombre}")
    print(f"  Fórmula (Matriz 3.1): {formula}")
    print(f"  Fuente de datos:      {fuente}")
    todo_ok = True
    for inc, meta_matriz in ((1, meta1), (2, meta2)):
        raiz = raices[inc]
        num, den, valor = calcular(raiz, inc)
        herramienta, advertencia = valor_herramienta(metrica, raiz, inc)
        op, objetivo = g.METAS[metrica][inc]
        coincide = (valor is None and herramienta is None) or (
            valor is not None and herramienta is not None and abs(valor - herramienta) < 1e-6
        )
        cumple = _cumple(valor, inc, metrica)
        if advertencia:
            estado = f"NO ACREDITA ({advertencia})"
        else:
            estado = {True: "CUMPLE", False: "NO CUMPLE", None: "PENDIENTE"}[cumple]
        texto = "sin dato" if valor is None else formato.format(valor)
        print(f"  Incremento {inc} ({'v1.0-PMV' if inc == 1 else 'main'})")
        print(f"    Numerador:    {num}")
        print(f"    Denominador:  {den}")
        print(f"    Resultado:    {texto}")
        print(
            f"    Meta Matriz 3.1: {meta_matriz}  ·  meta en gqm_metrics.py: {op} {formato.format(objetivo)}"
        )
        print(f"    gqm_metrics.py reporta: {'sin dato' if herramienta is None else formato.format(herramienta)}"
              f"  ->  {'COINCIDE' if coincide else 'NO COINCIDE'}")  # fmt: skip
        print(f"    Estado: {estado}")
        todo_ok &= coincide
    print()
    return todo_ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verifica las fórmulas GQM de la Matriz 3.1")
    parser.add_argument("--inc1", type=Path, required=True, help="checkout del tag v1.0-PMV")
    parser.add_argument("--inc2", type=Path, default=RAIZ)
    parser.add_argument("--metrica", choices=list(MATRIZ), help="solo una métrica")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raices = {1: args.inc1.resolve(), 2: args.inc2.resolve()}
    metricas = [args.metrica] if args.metrica else list(MATRIZ)
    ok = all([verificar(m, raices) for m in metricas])
    print("Todas las fórmulas coinciden con gqm_metrics.py." if ok else "HAY DIFERENCIAS.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
