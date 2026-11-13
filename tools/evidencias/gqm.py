"""Evidencias ejecutadas de M2.1, M2.2 y M3.1 (GQM) leyendo el repositorio y GitHub.

Uso: python tools/evidencias/gqm.py m21|m22|m31   (m22 usa la CLI gh con GH_TOKEN).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")
R = Path(__file__).resolve().parents[2]
TAGS = {1: "v1.0-PMV", 2: "v2.0-Inc2", 3: "v3.0-Inc3"}
RF = {1: [1, 2, 3, 4], 2: [5, 6, 7, 8], 3: [9, 10, 11]}


def git(*a):
    return subprocess.run(
        ["git", *a], cwd=R, capture_output=True, text=True, encoding="utf-8"
    ).stdout


modo = sys.argv[1]
if modo == "m21":
    for n, tag in TAGS.items():
        archivos = [
            a
            for a in git("ls-tree", "-r", "--name-only", tag, f"evidencias/inc{n}").split()
            if a.endswith(".png")
        ]
        esperadas = [
            f"evidencias/inc{n}/RF{rf:02d}_paso{k}_{s}.png"
            for rf in RF[n]
            for k, s in ((1, "entrada"), (2, "resultado"))
        ]
        ok = [e for e in esperadas if e in archivos]
        print(
            f"{tag}: git ls-tree evidencias/inc{n}  →  {len(ok)} de {len(esperadas)} capturas esperadas  ·  M2.1 = {100 * len(ok) / len(esperadas):.0f} %"
        )
        for e in esperadas:
            print(f"   {'✓' if e in archivos else '✗'} {e}")
elif modo == "m22":
    for n, tag in TAGS.items():
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
                f"inc{n}",
                "--json",
                "number,title,state",
            ],
            cwd=R,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        bugs = json.loads(r.stdout)
        print(
            f"Incremento {n} ({tag}): {len(bugs)} defecto(s) / {len(RF[n])} RF  →  M2.2 = {len(bugs) / len(RF[n]):.2f} Def/RF"
        )
        for b in sorted(bugs, key=lambda x: x["number"]):
            print(f"   #{b['number']:<3} {b['state']:<6} {b['title'][:95]}")
elif modo == "m31":
    brechas = yaml.safe_load((R / "docs/gqm/brechas.yaml").read_text(encoding="utf-8"))["brechas"]
    texto = "\n".join(p.read_text(encoding="utf-8") for p in (R / "tests").rglob("*.py"))
    ids = set(re.findall(r"CP[-_]RF(\d{2})[-_](\d{2})", texto))
    print("Brecha  Inc.  RF        Capturas  Pruebas CP-RFxx-01/02   Resuelta y verificada")
    total = 0
    for b in brechas:
        rfs = [int(r.split("-")[1]) for r in b["rf"]]
        inc = b["resuelta_en"]
        caps = all(
            (R / f"evidencias/inc{inc}/RF{r:02d}_paso{k}_{s}.png").is_file()
            for r in rfs
            for k, s in ((1, "entrada"), (2, "resultado"))
        )
        pruebas = all({(f"{r:02d}", "01"), (f"{r:02d}", "02")} <= ids for r in rfs)
        total += caps and pruebas
        print(
            f"{b['id']:<7} {inc:<5} {', '.join(b['rf']):<9} {'sí' if caps else 'NO':<9} {'sí' if pruebas else 'NO':<23} {'✓' if caps and pruebas else '✗'}  {b['descripcion']}"
        )
    print(
        f"\nM3.1 = {total} de {len(brechas)} brechas resueltas y verificadas = {100 * total / len(brechas):.0f} %"
    )
