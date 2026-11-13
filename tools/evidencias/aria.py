"""WCAG 4.1.2 y 1.4.1: árbol de accesibilidad que recibe un lector de pantalla (Chromium) en la
app desplegada, y textos que acompañan a cada color de estado.

Uso: docker compose up -d --build && python tools/evidencias/aria.py login|panel|color
"""

import re
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
URL = "http://localhost:8000"
modo = sys.argv[1]
with sync_playwright() as p:
    nav = p.chromium.launch()
    pag = nav.new_page(viewport={"width": 1366, "height": 900})
    pag.goto(f"{URL}/login")
    if modo == "login":
        print("Árbol de accesibilidad de /login (lo que anuncia un lector de pantalla):\n")
        print(pag.locator("body").aria_snapshot())
    pag.fill("input[name=nombre_usuario]", "operario")
    pag.fill("input[name=password]", "Oper123!")
    pag.click("button[type=submit]")
    pag.wait_for_url("**/panel")
    pag.wait_for_timeout(1200)
    if modo == "panel":
        print(
            "Árbol de accesibilidad del panel: enlace de salto, navegación y tarjeta de la Jaula J1:\n"
        )
        arbol = pag.locator("body").aria_snapshot()
        lineas = arbol.splitlines()
        fin_nav = next(i for i, ln in enumerate(lineas) if "main" in ln)
        print("\n".join(lineas[: fin_nav + 1]))
        print("  …")
        print(pag.locator('[data-estanque="3"]').aria_snapshot())
    if modo == "color":
        print(
            "WCAG 1.4.1: cada color de estado va acompañado de texto (no se depende solo del color)"
        )
        for ruta in ("/panel", "/alertas"):
            pag.goto(f"{URL}{ruta}")
            pag.wait_for_timeout(800)
            print(f"\n{ruta}")
            vistos = set()
            for el in pag.locator(".etiqueta").all():
                clase = (el.get_attribute("class") or "").replace("etiqueta", "").strip()
                color = el.evaluate("e => getComputedStyle(e).backgroundColor")
                texto = re.sub(r"\s+", " ", el.inner_text()).strip()[:40]
                if (clase, texto) in vistos or not texto:
                    continue
                vistos.add((clase, texto))
                print(f"  clase={clase:<22} fondo={color:<20} texto visible=«{texto}»")
    nav.close()
