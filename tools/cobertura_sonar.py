"""Ejecuta las pruebas unitarias y de integración y deja coverage-sonar.xml para SonarQube.

coverage.py escribe en <source> la ruta absoluta de la máquina (p. ej. D:/.../src); el escáner
corre en un contenedor con el proyecto en /usr/src, así que la ruta se reescribe a «src»,
relativa a la raíz del proyecto, que SonarQube resuelve en cualquier máquina.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "coverage-sonar.xml"


def main() -> int:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit", "tests/integration", "-q",
         "--cov=src", f"--cov-report=xml:{SALIDA}"],
        cwd=RAIZ,
    )  # fmt: skip
    if r.returncode != 0:
        return r.returncode
    xml = SALIDA.read_text(encoding="utf-8")
    xml = re.sub(r"<source>[^<]*</source>", "<source>src</source>", xml)
    SALIDA.write_text(xml, encoding="utf-8")
    print(f"Cobertura para SonarQube en {SALIDA.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
