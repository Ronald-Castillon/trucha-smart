"""Resume en Markdown los reportes de SciTools Understand (guía S14).

Lee metricas.csv y dependencias_archivos.csv generados por `und` y escribe README.md con:
métricas del proyecto, complejidad ciclomática de funciones y métodos, métricas de clases y
dependencias entre capas de la arquitectura hexagonal (domain → ports → adapters).

Uso: python tools/understand/resumen.py --salida docs/understand --codigo <checkout analizado>
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

CAPAS = ("domain", "ports", "adapters", "main", "tools")
# Reglas de pyproject.toml (import-linter, ADR-001): el dominio y los puertos forman el núcleo
# y no conocen a los adaptadores; los servicios del dominio usan las interfaces de los puertos.
PERMITIDAS = {
    "domain": {"domain", "ports"},
    "ports": {"ports", "domain"},
    "adapters": {"adapters", "ports", "domain"},
    "main": set(CAPAS),
    "tools": set(CAPAS),
}
FUNCIONES = {"Function", "Static Function", "Method", "Public Method", "Private Method"}


def numero(valor: str) -> float:
    """Understand usa la configuración regional (en español, coma decimal)."""
    valor = (valor or "").strip().replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return 0.0


def capa(ruta: Path, codigo: Path) -> str:
    partes = ruta.relative_to(codigo).parts
    if partes[0] == "tools":
        return "tools"
    if partes[:2] == ("src", "main.py"):
        return "main"
    return partes[1] if len(partes) > 1 and partes[1] in CAPAS else "otro"


def mapa_capas(codigo: Path) -> dict[str, str]:
    """Nombre corto del archivo → capa (solo si el nombre no es ambiguo entre capas)."""
    candidatos: dict[str, set[str]] = defaultdict(set)
    for base in ("src", "tools"):
        for ruta in (codigo / base).rglob("*.py"):
            candidatos[ruta.name].add(capa(ruta, codigo))
    return {n: next(iter(c)) for n, c in candidatos.items() if len(c) == 1}


def tabla(cabecera: list[str], filas: list[list[str]]) -> str:
    lineas = ["| " + " | ".join(cabecera) + " |", "|" + "---|" * len(cabecera)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--codigo", type=Path, required=True)
    args = parser.parse_args(argv)

    filas = list(csv.DictReader((args.salida / "metricas.csv").open(encoding="utf-8-sig")))
    archivos = [f for f in filas if f["Kind"] == "Module File"]
    clases = [f for f in filas if f["Kind"] == "Class"]
    funciones = [f for f in filas if f["Kind"] in FUNCIONES]
    tipos = Counter(f["Kind"] for f in filas)

    def suma(lista, clave):
        return int(sum(numero(f[clave]) for f in lista))

    loc, comentarios = suma(archivos, "CountLineCode"), suma(archivos, "CountLineComment")
    ciclo = [numero(f["Cyclomatic"]) for f in funciones]
    altas = [c for c in ciclo if c > 10]

    s = ["# Análisis estático con SciTools Understand (guía S14)\n\n"]
    s.append(
        f"Generado por `tools/understand/analizar.ps1` en GitHub Actions "
        f"({datetime.now(UTC):%d/%m/%Y %H:%M} UTC). "
        f"Corrida: {os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/"
        f"{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}\n\n"
    )
    s.append(
        "Alcance: `src/` (arquitectura hexagonal) y `tools/`, lenguaje Python. Herramienta: "
        "SciTools Understand 8.1 con licencia educativa, en el runner propio del equipo.\n"
    )
    s.append("\n## 1. Métricas del proyecto\n\n")
    s.append(tabla(["Métrica", "Valor"], [
        ["Archivos de código (Module File)", len(archivos)],
        ["Clases", len(clases)],
        ["Funciones y métodos", len(funciones)],
        ["Líneas totales (CountLine)", suma(archivos, "CountLine")],
        ["Líneas de código (CountLineCode)", loc],
        ["Líneas de comentario (CountLineComment)", comentarios],
        ["Relación comentario/código", f"{comentarios / loc:.2f}" if loc else "—"],
        ["Complejidad ciclomática promedio por función", f"{sum(ciclo) / len(ciclo):.2f}" if ciclo else "—"],
        ["Complejidad ciclomática máxima", int(max(ciclo, default=0))],
        ["Funciones con complejidad > 10", f"{len(altas)} de {len(funciones)}"],
    ]))  # fmt: skip
    s.append(
        "\nEntidades exportadas por tipo: "
        + ", ".join(f"{k} {v}" for k, v in sorted(tipos.items()))
        + ".\n"
    )

    s.append("\n## 2. Métricas por capa (Architecture)\n\n")
    por_capa: dict[str, list[dict]] = defaultdict(list)
    nombres = mapa_capas(args.codigo)
    for f in archivos:
        por_capa[nombres.get(f["Name"], "otro")].append(f)
    s.append(tabla(["Capa", "Archivos", "Líneas de código", "Complejidad total (SumCyclomatic)"], [
        [c, len(por_capa[c]), suma(por_capa[c], "CountLineCode"), suma(por_capa[c], "SumCyclomatic")]
        for c in (*CAPAS, "otro") if por_capa.get(c)
    ]))  # fmt: skip

    s.append("\n## 3. Function Metrics · 10 funciones de mayor complejidad ciclomática\n\n")
    top = sorted(
        funciones, key=lambda f: (numero(f["Cyclomatic"]), numero(f["CountLineCode"])), reverse=True
    )[:10]
    s.append(tabla(["Función", "Ciclomática", "Líneas de código", "Anidamiento máx."], [
        [f"`{f['Name']}`", int(numero(f["Cyclomatic"])), int(numero(f["CountLineCode"])), int(numero(f["MaxNesting"]))]
        for f in top
    ]))  # fmt: skip

    s.append("\n## 4. Class Metrics · 10 clases con más acoplamiento\n\n")
    topc = sorted(
        clases,
        key=lambda f: (numero(f["CountClassCoupled"]), numero(f["CountDeclMethod"])),
        reverse=True,
    )[:10]
    s.append(tabla(["Clase", "Acoplamiento (CBO)", "Métodos", "Herencia máx.", "Líneas de código"], [
        [f"`{f['Name']}`", int(numero(f["CountClassCoupled"])), int(numero(f["CountDeclMethod"])),
         int(numero(f["MaxInheritanceTree"])), int(numero(f["CountLineCode"]))]
        for f in topc
    ]))  # fmt: skip

    s.append("\n## 5. Dependencies · dependencias entre capas\n\n")
    matriz: Counter[tuple[str, str]] = Counter()
    violaciones = []
    deps = csv.DictReader((args.salida / "dependencias_archivos.csv").open(encoding="utf-8-sig"))
    for d in deps:
        origen, destino = nombres.get(d["From File"]), nombres.get(d["To File"])
        if not origen or not destino:
            continue
        refs = int(numero(d["References"]))
        matriz[(origen, destino)] += refs
        if destino not in PERMITIDAS.get(origen, set()):
            violaciones.append([d["From File"], origen, d["To File"], destino, refs])
    usadas = [c for c in CAPAS if any(c in par for par in matriz)]
    s.append("Referencias desde la capa de la fila hacia la capa de la columna:\n\n")
    s.append(
        tabla(
            ["Desde \\ Hacia", *usadas],
            [[o, *[matriz.get((o, d), 0) or "·" for d in usadas]] for o in usadas],
        )
    )
    s.append(
        f"\n**Regla de la arquitectura hexagonal (ADR-001, contratos de import-linter en "
        f"pyproject.toml):** `domain` y `ports` no dependen de `adapters` ni de `main`. "
        f"Dependencias que la violan según Understand: **{len(violaciones)}**.\n"
    )
    if violaciones:
        s.append(
            "\n" + tabla(["Archivo", "Capa", "Depende de", "Capa", "Referencias"], violaciones)
        )

    s.append("\n## 6. Archivos del reporte\n\n")
    s.append(tabla(["Archivo", "Contenido"], [
        ["[metricas.csv](metricas.csv)", "Todas las métricas por entidad (`und metrics`)"],
        ["[dependencias_archivos.csv](dependencias_archivos.csv)", "Dependencias entre archivos (`und export -dependencies file csv`)"],
        ["[dependencias_clases.csv](dependencias_clases.csv)", "Dependencias entre clases (`und export -dependencies class csv`)"],
        ["[reporte_understand.txt](reporte_understand.txt)", "Reportes Project/File/Class/Class OO/Program Unit Metrics, Complexity e Imports (`und report`)"],
        ["[html/](html/)", "Los mismos reportes en HTML"],
        ["[analisis.sarif](analisis.sarif)", "Errores y advertencias del análisis (`und analyze -sarif`)"],
    ]))  # fmt: skip
    (args.salida / "README.md").write_text("".join(s), encoding="utf-8", newline="\n")
    print("".join(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
