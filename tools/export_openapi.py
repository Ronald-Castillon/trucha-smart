"""Exporta el contrato OpenAPI de la aplicación a docs/openapi.json.

Uso:  python tools/export_openapi.py          # regenera el archivo
      python tools/export_openapi.py --check  # falla (exit 1) si el archivo está desactualizado
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "docs" / "openapi.json"
sys.path.insert(0, str(RAIZ))


def contrato_actual() -> str:
    from src.main import crear_app

    return json.dumps(crear_app().openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Exporta docs/openapi.json")
    parser.add_argument("--check", action="store_true", help="solo verificar, no escribir")
    args = parser.parse_args(argv)
    actual = contrato_actual()
    if args.check:
        guardado = DESTINO.read_text(encoding="utf-8") if DESTINO.exists() else ""
        if guardado != actual:
            print("docs/openapi.json está desactualizado: ejecuta python tools/export_openapi.py")
            return 1
        print("docs/openapi.json está actualizado.")
        return 0
    DESTINO.write_text(actual, encoding="utf-8")
    print(f"Escrito {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
