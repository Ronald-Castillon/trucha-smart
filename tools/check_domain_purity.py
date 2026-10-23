"""Verifica la pureza del dominio hexagonal (métrica M1.1).

Recorre con AST cada módulo .py de src/domain (y, como control adicional, src/ports) y
marca como "contaminado" todo módulo que importe algo que no sea:
  - la biblioteca estándar de Python (sys.stdlib_module_names), o
  - src.domain / src.ports (incluidas importaciones relativas que se resuelvan dentro de ellos).

Imprime  M1.1 = módulos contaminados / total de módulos de src/domain x 100
y termina con código 1 si M1.1 > 0 o si algún puerto está contaminado.

Uso:  python tools/check_domain_purity.py [--raiz .]
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

PERMITIDOS_INTERNOS = ("src.domain", "src.ports")


@dataclass
class ResultadoModulo:
    ruta: Path
    imports_prohibidos: list[str] = field(default_factory=list)

    @property
    def contaminado(self) -> bool:
        return bool(self.imports_prohibidos)


@dataclass
class ResultadoPaquete:
    paquete: str
    modulos: list[ResultadoModulo]

    @property
    def total(self) -> int:
        return len(self.modulos)

    @property
    def contaminados(self) -> list[ResultadoModulo]:
        return [m for m in self.modulos if m.contaminado]

    @property
    def porcentaje(self) -> float:
        return 0.0 if self.total == 0 else len(self.contaminados) / self.total * 100


def _nombre_modulo(raiz: Path, ruta: Path) -> str:
    partes = list(ruta.relative_to(raiz).with_suffix("").parts)
    if partes[-1] == "__init__":
        partes.pop()
    return ".".join(partes)


def _resolver_relativo(modulo_actual: str, es_paquete: bool, nivel: int, nombre: str | None) -> str:
    base = modulo_actual.split(".")
    if not es_paquete:
        base = base[:-1]
    if nivel > 1:
        base = base[: len(base) - (nivel - 1)]
    return ".".join(base + ([nombre] if nombre else []))


def _es_permitido(nombre: str) -> bool:
    if any(nombre == p or nombre.startswith(p + ".") for p in PERMITIDOS_INTERNOS):
        return True
    return nombre.split(".")[0] in sys.stdlib_module_names


def analizar_modulo(raiz: Path, ruta: Path) -> ResultadoModulo:
    modulo = _nombre_modulo(raiz, ruta)
    es_paquete = ruta.name == "__init__.py"
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    resultado = ResultadoModulo(ruta=ruta)
    for nodo in ast.walk(arbol):
        nombres: list[str] = []
        if isinstance(nodo, ast.Import):
            nombres = [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                nombres = [_resolver_relativo(modulo, es_paquete, nodo.level, nodo.module)]
            elif nodo.module:
                nombres = [nodo.module]
        for nombre in nombres:
            if not _es_permitido(nombre):
                resultado.imports_prohibidos.append(f"línea {nodo.lineno}: {nombre}")
    return resultado


def analizar_paquete(raiz: Path, paquete: str) -> ResultadoPaquete:
    carpeta = raiz / Path(*paquete.split("."))
    modulos = [analizar_modulo(raiz, p) for p in sorted(carpeta.rglob("*.py"))]
    return ResultadoPaquete(paquete=paquete, modulos=modulos)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raiz", default=Path(__file__).resolve().parent.parent, type=Path)
    args = parser.parse_args(argv)
    raiz: Path = args.raiz.resolve()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # consola de Windows

    dominio = analizar_paquete(raiz, "src.domain")
    puertos = analizar_paquete(raiz, "src.ports")

    for res in (dominio, puertos):
        print(f"{res.paquete}: {res.total} módulos, {len(res.contaminados)} contaminados")
        for m in res.contaminados:
            print(f"  ✗ {m.ruta.relative_to(raiz)}")
            for imp in m.imports_prohibidos:
                print(f"      {imp}")

    print(
        f"M1.1 = {len(dominio.contaminados)} / {dominio.total} x 100 = {dominio.porcentaje:.1f} %"
    )
    if dominio.contaminados or puertos.contaminados:
        print("FALLO: el dominio o los puertos importan dependencias no permitidas.")
        return 1
    print("OK: dominio y puertos usan solo la biblioteca estándar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
