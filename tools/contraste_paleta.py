"""RNF-U: verifica el contraste WCAG 2.1 (1.4.3, AA >= 4.5:1) de cada par texto/fondo de la paleta.

Lee las variables de :root en estilos.css y calcula la razón de contraste con la luminancia relativa
de WCAG: L = 0.2126 R + 0.7152 G + 0.0722 B (canales linealizados);
razón = (L1 + 0.05) / (L2 + 0.05).
Sale con código 1 si algún par usado para texto no alcanza 4.5:1.

Uso: python tools/contraste_paleta.py [--markdown]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "src/adapters/inbound/web/static/estilos.css"
MINIMO_AA = 4.5

# (texto, fondo, dónde se usa). "#fff" = blanco literal en estilos.css.
PARES = [
    ("texto", "fondo", "texto general sobre el fondo de la página"),
    ("texto", "superficie", "texto en tarjetas"),
    ("suave", "superficie", "texto secundario (.suave, etiquetas de formulario)"),
    ("suave", "fondo", "texto secundario fuera de tarjetas"),
    ("#ffffff", "primario", "menú superior y botones"),
    ("primario", "superficie", "botón secundario y enlaces"),
    ("#ffffff", "verde", "etiqueta / semáforo NORMAL"),
    ("texto", "amarillo", "etiqueta / semáforo PRECAUCIÓN (texto oscuro)"),
    ("#ffffff", "rojo", "etiqueta / semáforo CRÍTICA, botón detener simulador"),
    ("amarillo-texto", "superficie", "valor en nivel de precaución (.nivel-PRECAUCION)"),
    ("rojo", "superficie", "valor crítico, predicción de riesgo, bitácora"),
    ("verde", "superficie", "indicador 'en vivo'"),
    ("rojo", "#fdecea", "mensaje de error"),
    ("verde", "#e8f5ee", "mensaje de confirmación"),
]


def variables(css: str) -> dict[str, str]:
    raiz = re.search(r":root\s*\{(.*?)\}", css, re.S).group(1)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", raiz))


def luminancia(hexa: str) -> float:
    canales = [int(hexa[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(a: str, b: str) -> float:
    claro, oscuro = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    paleta = variables(CSS.read_text(encoding="utf-8"))

    def color(nombre: str) -> str:
        return nombre if nombre.startswith("#") else paleta[nombre]

    filas, fallos = [], 0
    for texto, fondo, uso in PARES:
        r = contraste(color(texto), color(fondo))
        ok = r >= MINIMO_AA
        fallos += not ok
        filas.append((texto, color(texto), fondo, color(fondo), r, ok, uso))
    if "--markdown" in sys.argv:
        print("| Texto | Fondo | Contraste | AA (≥ 4.5:1) | Uso |")
        print("|---|---|---:|:---:|---|")
        for t, tc, f, fc, r, ok, uso in filas:
            print(f"| {t} `{tc}` | {f} `{fc}` | {r:.2f}:1 | {'Sí' if ok else 'No'} | {uso} |")
    else:
        for t, tc, f, fc, r, ok, uso in filas:
            estado = "OK " if ok else "NO "
            print(f"{estado} {r:5.2f}:1  {t:<15} {tc}  sobre {f:<11} {fc}  ({uso})")
        print(f"\n{len(filas) - fallos}/{len(filas)} pares cumplen WCAG 2.1 AA (>= {MINIMO_AA}:1)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
