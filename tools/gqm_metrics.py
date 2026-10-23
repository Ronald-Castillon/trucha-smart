"""Calcula las métricas GQM de un incremento y escribe docs/gqm/reporte_incN.md.

Métricas:
  M1.1 Pureza del dominio           (módulos contaminados / total x 100)      meta = 0 %
  M1.2 Componentes hexagonales      (presentes y conformes / 5 x 100)         meta = 100 %
  M2.1 Evidencias                   (capturas existentes / esperadas x 100)   meta = 100 %
  M2.2 Densidad de defectos         (Issues bug del incremento / n.º de RF)   meta <= 1.0 / 0.2
  M2.3 Cobertura de src/domain      (desde coverage.xml)                      meta >= 80 %
  M3.1 Brechas resueltas            (resueltas verificadas / 10 x 100)        meta >= 60 / 90 %
  M3.2 Mejora de indicadores valor  (promedio IV-1..IV-3, % sobre AS-IS)      meta >= 50 / 80 %

Ningún valor se inventa: si falta un dato (coverage.xml, líneas base AS-IS, gh) se informa
"pendiente" o "no disponible".

Uso:  python tools/gqm_metrics.py --incremento 1
      (antes: pytest -m "not e2e" --cov=src/domain --cov-report=xml  y  pytest -m e2e)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from check_domain_purity import analizar_paquete  # noqa: E402

RF_POR_INCREMENTO = {1: [1, 2, 3, 4], 2: [5, 6, 7, 8]}
METAS = {
    "M1.1": {1: ("<=", 0.0), 2: ("<=", 0.0)},
    "M1.2": {1: (">=", 100.0), 2: (">=", 100.0)},
    "M2.1": {1: (">=", 100.0), 2: (">=", 100.0)},
    "M2.2": {1: ("<=", 1.0), 2: ("<=", 0.2)},
    "M2.3": {1: (">=", 80.0), 2: (">=", 80.0)},
    "M3.1": {1: (">=", 60.0), 2: (">=", 90.0)},
    "M3.2": {1: (">=", 50.0), 2: (">=", 80.0)},
}
COMPONENTES = {
    "domain/model": ["src/domain/model"],
    "domain/service": ["src/domain/service"],
    "ports/inbound": ["src/ports/inbound"],
    "ports/outbound": ["src/ports/outbound"],
    "adapters (inbound + outbound)": ["src/adapters/inbound", "src/adapters/outbound"],
}


@dataclass
class Metrica:
    id: str
    nombre: str
    valor: float | None
    formato: str
    detalle: str

    def texto_valor(self) -> str:
        return "pendiente" if self.valor is None else self.formato.format(self.valor)


def evaluar_meta(m: Metrica, inc: int) -> tuple[str, str]:
    op, objetivo = METAS[m.id][inc]
    meta = f"{op} {m.formato.format(objetivo)}"
    if m.valor is None:
        return meta, "⏳ pendiente"
    ok = m.valor <= objetivo if op == "<=" else m.valor >= objetivo
    return meta, "✅ cumple" if ok else "❌ no cumple"


# --------------------------------------------------------------------------- M1


def m1_1() -> Metrica:
    dom = analizar_paquete(RAIZ, "src.domain")
    det = f"{len(dom.contaminados)} de {dom.total} módulos de src/domain importan fuera de stdlib"
    if dom.contaminados:
        det += ": " + ", ".join(str(m.ruta.relative_to(RAIZ)) for m in dom.contaminados)
    return Metrica("M1.1", "Pureza del dominio", dom.porcentaje, "{:.1f} %", det)


def _modulos(carpeta: Path) -> list[Path]:
    return [p for p in carpeta.rglob("*.py") if p.name != "__init__.py"] if carpeta.exists() else []


def _import_linter_ok() -> bool | None:
    exe = shutil.which("lint-imports")
    if exe is None:
        return None
    r = subprocess.run([exe], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    return r.returncode == 0


def m1_2() -> Metrica:
    contratos = _import_linter_ok()
    contaminados = {
        p.resolve()
        for paq in ("src.domain", "src.ports")
        for p in (m.ruta for m in analizar_paquete(RAIZ, paq).contaminados)
    }
    conformes = 0
    partes = []
    for nombre, carpetas in COMPONENTES.items():
        presentes = all(_modulos(RAIZ / c) for c in carpetas)
        puros = not any(p.resolve() in contaminados for c in carpetas for p in _modulos(RAIZ / c))
        ok = presentes and puros and contratos is not False
        conformes += ok
        estado = "OK" if ok else ("sin módulos" if not presentes else "no conforme")
        partes.append(f"{nombre}: {estado}")
    det = "; ".join(partes)
    det += {True: "; import-linter: OK", False: "; import-linter: FALLA", None: ""}[contratos]
    return Metrica(
        "M1.2", "Componentes hexagonales conformes", conformes / 5 * 100, "{:.0f} %", det
    )


# --------------------------------------------------------------------------- M2


def capturas_esperadas(inc: int) -> list[Path]:
    return [
        RAIZ / "evidencias" / f"inc{inc}" / f"RF{rf:02d}_paso{n}_{s}.png"
        for rf in RF_POR_INCREMENTO[inc]
        for n, s in ((1, "entrada"), (2, "resultado"))
    ]


def m2_1(inc: int) -> Metrica:
    esperadas = capturas_esperadas(inc)
    existentes = [p for p in esperadas if p.is_file() and p.stat().st_size > 0]
    faltan = [p.name for p in esperadas if p not in existentes]
    det = f"{len(existentes)} de {len(esperadas)} capturas en evidencias/inc{inc}/"
    if faltan:
        det += " · faltan: " + ", ".join(faltan)
    return Metrica(
        "M2.1", "Evidencias de aceptación", len(existentes) / len(esperadas) * 100, "{:.0f} %", det
    )


def _bugs_gh(inc: int) -> list[str] | None:
    if shutil.which("gh") is None:
        return None
    r = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--state",
            "all",
            "--label",
            "bug",
            "--label",
            f"inc{inc}",
            "--limit",
            "500",
            "--json",
            "number,title",
        ],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode != 0:
        return None
    return [f"#{i['number']} {i['title']}" for i in json.loads(r.stdout or "[]")]


def _bugs_csv(inc: int) -> list[str]:
    ruta = RAIZ / "docs" / "gqm" / "defectos.csv"
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8", newline="") as f:
        return [
            f"{r['id']} {r['titulo']}"
            for r in csv.DictReader(f)
            if str(r.get("incremento", "")).strip() == str(inc)
        ]


def m2_2(inc: int) -> Metrica:
    bugs = _bugs_gh(inc)
    fuente = f"GitHub Issues (label bug + inc{inc})"
    if bugs is None:
        bugs, fuente = _bugs_csv(inc), "docs/gqm/defectos.csv"
    n_rf = len(RF_POR_INCREMENTO[inc])
    det = f"{len(bugs)} defectos / {n_rf} RF · fuente: {fuente}"
    if bugs:
        det += " · " + "; ".join(bugs)
    return Metrica("M2.2", "Densidad de defectos", len(bugs) / n_rf, "{:.2f} Def/RF", det)


def m2_3() -> Metrica:
    ruta = RAIZ / "coverage.xml"
    if not ruta.exists():
        return Metrica(
            "M2.3",
            "Cobertura de src/domain",
            None,
            "{:.1f} %",
            "coverage.xml no encontrado: ejecutar pytest con --cov-report=xml",
        )
    raiz_xml = ET.parse(ruta).getroot()
    # Las rutas de <class filename> son relativas a <source>; se reconstruye la ruta completa
    # para quedarse solo con los archivos de src/domain.
    fuentes = [s.text.replace("\\", "/").rstrip("/") for s in raiz_xml.iter("source") if s.text]
    total = cubiertas = 0
    for clase in raiz_xml.iter("class"):
        archivo = clase.get("filename", "").replace("\\", "/")
        completas = [f"{f}/{archivo}" for f in fuentes] or [archivo]
        if not any("src/domain/" in c or c.startswith("domain/") for c in completas):
            continue
        for linea in clase.iter("line"):
            total += 1
            cubiertas += int(linea.get("hits", "0")) > 0
    if total == 0:
        return Metrica(
            "M2.3",
            "Cobertura de src/domain",
            None,
            "{:.1f} %",
            "coverage.xml no contiene líneas de src/domain",
        )
    return Metrica(
        "M2.3",
        "Cobertura de src/domain (líneas)",
        cubiertas / total * 100,
        "{:.1f} %",
        f"{cubiertas} de {total} líneas ejecutables cubiertas",
    )


# --------------------------------------------------------------------------- M3


def _ids_en_pruebas() -> set[str]:
    patron = re.compile(r"CP[-_]RF(\d{2})[-_](\d{2})")
    ids = set()
    for p in (RAIZ / "tests").rglob("*.py"):
        for a, b in patron.findall(p.read_text(encoding="utf-8")):
            ids.add(f"RF-{a}:{b}")
    return ids


def m3_1(inc: int) -> Metrica:
    datos = yaml.safe_load((RAIZ / "docs" / "gqm" / "brechas.yaml").read_text(encoding="utf-8"))
    ids = _ids_en_pruebas()
    resueltas, notas = [], []
    for b in datos["brechas"]:
        r_en = b.get("resuelta_en")
        if r_en is None or r_en > inc:
            continue
        faltas = []
        for rf in b["rf"]:
            n = int(rf.split("-")[1])
            ev = RAIZ / "evidencias" / f"inc{1 if n <= 4 else 2}"
            if not all(
                (ev / f"RF{n:02d}_paso{k}_{s}.png").is_file()
                for k, s in ((1, "entrada"), (2, "resultado"))
            ):
                faltas.append(f"{rf} sin capturas")
            if not {f"{rf}:01", f"{rf}:02"} <= ids:
                faltas.append(f"{rf} sin pruebas CP")
        if faltas:
            notas.append(f"{b['id']} declarada pero no verificada ({', '.join(faltas)})")
        else:
            resueltas.append(b["id"])
    total = len(datos["brechas"])
    det = f"{len(resueltas)} de {total} resueltas y verificadas: {', '.join(resueltas) or '—'}"
    if notas:
        det += " · " + "; ".join(notas)
    return Metrica("M3.1", "Brechas AS-IS resueltas", len(resueltas) / total * 100, "{:.0f} %", det)


def m3_2(inc: int) -> Metrica:
    datos = yaml.safe_load(
        (RAIZ / "docs" / "gqm" / "valor_indicadores.yaml").read_text(encoding="utf-8")
    )
    mejoras, partes = [], []
    for iv in datos["indicadores"]:
        as_is, to_be = iv.get("as_is"), iv.get(f"to_be_inc{inc}")
        if as_is in (None, "") or to_be in (None, "") or float(as_is) == 0:
            partes.append(f"{iv['id']}: pendiente (falta AS-IS o TO-BE)")
            continue
        a, t = float(as_is), float(to_be)
        mejora = (a - t) / a * 100 if iv["sentido"] == "menor_es_mejor" else (t - a) / a * 100
        mejoras.append(mejora)
        partes.append(f"{iv['id']}: {a:g} → {t:g} {iv['unidad']} ({mejora:.1f} %)")
    completos = len(mejoras) == len(datos["indicadores"])
    valor = sum(mejoras) / len(mejoras) if completos else None
    return Metrica("M3.2", "Mejora de indicadores de valor", valor, "{:.1f} %", "; ".join(partes))


# --------------------------------------------------------------------------- reporte


def generar_reporte(inc: int) -> str:
    metricas = [m1_1(), m1_2(), m2_1(inc), m2_2(inc), m2_3(), m3_1(inc), m3_2(inc)]
    lineas = [
        f"# Reporte GQM — Incremento {inc}",
        "",
        f"Generado por `tools/gqm_metrics.py --incremento {inc}` el "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}.",
        "Los valores se calculan a partir de artefactos reales del repositorio "
        "(código, coverage.xml, evidencias/, Issues/defectos.csv, docs/gqm/*.yaml).",
        "",
        "| Métrica | Nombre | Valor | Meta | Estado |",
        "|---|---|---|---|---|",
    ]
    for m in metricas:
        meta, estado = evaluar_meta(m, inc)
        lineas.append(f"| {m.id} | {m.nombre} | {m.texto_valor()} | {meta} | {estado} |")
    lineas += ["", "## Detalle", ""]
    for m in metricas:
        lineas.append(f"- **{m.id}** — {m.detalle}")
    lineas.append("")
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Métricas GQM por incremento")
    parser.add_argument("--incremento", type=int, choices=(1, 2), required=True)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    texto = generar_reporte(args.incremento)
    destino = RAIZ / "docs" / "gqm" / f"reporte_inc{args.incremento}.md"
    destino.write_text(texto, encoding="utf-8", newline="\n")
    print(texto)
    print(f"Escrito {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
