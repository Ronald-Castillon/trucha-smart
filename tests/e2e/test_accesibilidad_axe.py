"""RNF-U: auditoría automatizada WCAG 2.1 A/AA con axe-core en todas las pantallas (Issue #30).

Genera evidencias/inc3/axe/resultados.json y resumen.md con lo medido en cada ejecución.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import axe_playwright_python
import pytest

from tests.e2e.conftest import EVIDENCIAS
from tests.e2e.test_rf01_autenticacion import iniciar_sesion

AXE_JS = Path(axe_playwright_python.__file__).parent / "axe.min.js"
ETIQUETAS_WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
PANTALLAS = [
    ("Inicio de sesión", "/login", None),
    ("Panel en vivo", "/panel", "admin"),
    ("Registrar lectura", "/lecturas/nueva", "admin"),
    ("Estanques", "/estanques", "admin"),
    ("Detalle de estanque", "/estanques/1", "admin"),
    ("Historial y predicción", "/estanques/1/historial?desde=2026-10-16&hasta=2026-10-22", "admin"),
    ("Producción del lote (FCR)", "/lotes/1/produccion", "admin"),
    ("Alertas", "/alertas", "admin"),
    ("Reportes", "/reportes", "admin"),
    ("Usuarios", "/usuarios", "admin"),
    ("Integraciones", "/integraciones", "admin"),
    ("Auditoría", "/auditoria", "admin"),
]
SALIDA = EVIDENCIAS / "inc3" / "axe"
_resultados: list[dict] = []


def auditar(pagina) -> dict:
    pagina.add_script_tag(path=str(AXE_JS))
    return pagina.evaluate(
        """etiquetas => axe.run(document, {runOnly: {type: 'tag', values: etiquetas},
                                         resultTypes: ['violations', 'passes']})""",
        ETIQUETAS_WCAG,
    )


@pytest.mark.parametrize(("nombre", "ruta", "usuario"), PANTALLAS, ids=[p[1] for p in PANTALLAS])
def test_pantalla_sin_violaciones_wcag_a_aa(pagina, nombre, ruta, usuario):
    if usuario:
        iniciar_sesion(pagina, "admin", "Admin123!")
        pagina.wait_for_url("**/panel")
    pagina.goto(ruta)
    pagina.wait_for_load_state("networkidle")
    r = auditar(pagina)
    violaciones = [
        {
            "regla": v["id"],
            "impacto": v["impact"],
            "descripcion": v["help"],
            "nodos": [n["target"] for n in v["nodes"]][:5],
        }
        for v in r["violations"]
    ]
    _resultados.append(
        {
            "pantalla": nombre,
            "ruta": ruta,
            "reglas_aprobadas": len(r["passes"]),
            "violaciones": violaciones,
            "axe": r["testEngine"]["version"],
        }
    )
    _guardar()
    assert violaciones == [], json.dumps(violaciones, ensure_ascii=False, indent=1)


def _guardar() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    datos = {
        "ejecutado_en": datetime.now(UTC).isoformat(timespec="seconds"),
        "etiquetas": ETIQUETAS_WCAG,
        "pantallas": _resultados,
    }
    (SALIDA / "resultados.json").write_text(
        json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    filas = [
        f"| {p['pantalla']} | `{p['ruta'].split('?')[0]}` | {p['reglas_aprobadas']} "
        f"| {len(p['violaciones'])} |"
        for p in _resultados
    ]
    total = sum(len(p["violaciones"]) for p in _resultados)
    (SALIDA / "resumen.md").write_text(
        "\n".join(
            [
                "# Auditoría axe-core (WCAG 2.0/2.1 A y AA)",
                "",
                f"Generado por `tests/e2e/test_accesibilidad_axe.py` el {datos['ejecutado_en']} "
                f"con axe-core {_resultados[0]['axe']}.",
                "",
                "| Pantalla | Ruta | Reglas aprobadas | Violaciones |",
                "|---|---|---:|---:|",
                *filas,
                "",
                f"**Total de violaciones: {total}** en {len(_resultados)} pantallas.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_teclado_saltar_al_contenido_y_foco_visible(pagina):
    """WCAG 2.1.1, 2.4.1 y 2.4.7: el primer Tab muestra el enlace de salto y el foco se ve."""
    iniciar_sesion(pagina, "admin", "Admin123!")
    pagina.wait_for_url("**/panel")
    pagina.keyboard.press("Tab")
    enlace = pagina.locator("a.saltar")
    assert enlace.evaluate("e => e === document.activeElement")
    assert enlace.bounding_box()["x"] >= 0  # visible al recibir el foco
    estilo = enlace.evaluate("e => getComputedStyle(e).outlineStyle")
    assert estilo == "solid"
    pagina.keyboard.press("Enter")
    assert pagina.evaluate("document.activeElement.id") == "contenido"


MOVIL = ["/usuarios", "/alertas", "/auditoria", "/estanques", "/integraciones"]


@pytest.mark.parametrize("ruta", MOVIL)
def test_tablas_en_movil_sin_violaciones(navegador, url_base, ruta):
    """A 375 px las tablas desbordan: su zona desplazable debe poder usarse con teclado (#38)."""
    contexto = navegador.new_context(base_url=url_base, viewport={"width": 375, "height": 740})
    pagina = contexto.new_page()
    try:
        iniciar_sesion(pagina, "admin", "Admin123!")
        pagina.wait_for_url("**/panel")
        pagina.goto(ruta)
        pagina.wait_for_load_state("networkidle")
        violaciones = [
            (v["id"], [n["target"] for n in v["nodes"]]) for v in auditar(pagina)["violations"]
        ]
        assert violaciones == []
    finally:
        contexto.close()
