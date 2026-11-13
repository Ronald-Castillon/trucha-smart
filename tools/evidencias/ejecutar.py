"""Ejecuta las evidencias del Informe Integrador S12 y guarda cada salida como una página Markdown.

Lo usa el workflow «Evidencias del informe» (.github/workflows/evidencias.yml) en GitHub Actions:
cada evidencia queda en evidencias/ejecuciones/<nombre>.md con el comando, la salida literal, el
código de salida y los datos de la ejecución (número de corrida, enlace, commit y fecha).

Las evidencias de calidad del producto se ejecutan sobre el tag v3.0-Inc3 (el alcance evaluado en
el informe); las de despliegue y seguridad en ejecución, sobre la rama main y su imagen Docker.

Uso: python tools/evidencias/ejecutar.py --tag-dir ../tag-v3.0-Inc3 --salida evidencias/ejecuciones
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ANSI = re.compile(r"\x1b\[[0-9;]*m")
JWT = re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+")  # tokens de sesión: se ocultan
RENDER = "https://truchasmart.onrender.com"
LOGIN = "nombre_usuario=piscicultor&password=Pisci123!"

TAGS = {"tag1": "v1.0-PMV", "tag2": "v2.0-Inc2", "tag": "v3.0-Inc3"}


def _gqm(n: int, donde: str) -> list[tuple[str, str, str, str]]:
    """Métricas GQM ejecutadas con las herramientas que contiene cada versión (Eje 6)."""
    tag = TAGS[donde]
    return [
        (
            f"gqm{n}_pureza",
            f"GQM M1.1 · pureza del dominio en {tag}",
            donde,
            "python tools/check_domain_purity.py",
        ),
        (
            f"gqm{n}_lint",
            f"GQM M1.2 · contratos de arquitectura (import-linter) en {tag}",
            donde,
            "lint-imports",
        ),
        (
            f"gqm{n}_pytest",
            f"GQM M2.3 · pruebas y cobertura de src/domain en {tag}",
            donde,
            'python -m pytest -m "not e2e" -q -p no:warnings --cov=src/domain --cov-report=term --cov-report=xml',
        ),
        (
            f"gqm{n}_reporte",
            f"Reporte GQM M1.1–M3.2 del Incremento {n} ({tag})",
            donde,
            f"python tools/gqm_metrics.py --incremento {n} > /dev/null && cat docs/gqm/reporte_inc{n}.md",
        ),
        (
            f"gqm{n}_valor",
            f"GQM M3.2 · indicadores de valor TO-BE medidos sobre {tag}",
            "main",
            f"python tools/medir_indicadores.py --etiqueta github_inc{n} --repo {{{donde}}}",
        ),
    ]


# (nombre, título, dónde: "tag1", "tag2", "tag" (v3.0-Inc3) o "main", comando bash)
EVIDENCIAS: list[tuple[str, str, str, str]] = [
    *_gqm(1, "tag1"),
    *_gqm(2, "tag2"),
    *_gqm(3, "tag"),
    # ---- calidad del producto (tag v3.0-Inc3)
    ("x_ruff", "Linter ruff: estilo y formato", "tag", "ruff check . && ruff format --check ."),
    ("s_pytest", "Pruebas unitarias e integración con cobertura del dominio (M2.3)", "tag",
     'python -m pytest -m "not e2e" -q -p no:warnings --cov=src/domain --cov-branch --cov-report=term'),
    ("r_salud", "R · /api/salud responde 503 sin caerse cuando falla la base de datos", "tag",
     "python -m pytest tests/integration/test_salud.py -p no:warnings -v"),
    ("u_contraste", "U · Contraste de la paleta (WCAG 2.1 AA, 1.4.3)", "tag", "python tools/contraste_paleta.py"),
    ("u_axe", "U · axe-core en las pantallas, móvil a 375 px y teclado", "tag",
     "python -m pytest tests/e2e/test_accesibilidad_axe.py -m e2e -p no:warnings -v"),
    ("f_e2e_rf", "F · Pruebas E2E de aceptación de cada requisito funcional", "tag",
     'python -m pytest tests/e2e -m e2e -p no:warnings -v -k "rf"'),
    ("mas_bandit", "+ · SAST con Bandit (severidad media o alta)", "tag", "bandit -r src -ll"),
    ("mas_seguridad", "+ · Pruebas de cabeceras, auditoría y configuración segura", "tag",
     "python -m pytest tests/integration/test_seguridad_http.py tests/integration/test_api_auditoria.py "
     "tests/unit/test_seguridad.py -p no:warnings -v"),
    ("mas_openapi", "+ · Contrato OpenAPI al día", "tag", "python tools/export_openapi.py --check"),
    # ---- métricas GQM (leen los tags y GitHub)
    ("g_m21", "GQM M2.1 · capturas de aceptación en cada tag", "main", "python tools/evidencias/gqm.py m21"),
    ("g_m22", "GQM M2.2 · defectos registrados por incremento", "main", "python tools/evidencias/gqm.py m22"),
    ("g_m31", "GQM M3.1 · brechas AS-IS con capturas y casos de prueba", "main", "python tools/evidencias/gqm.py m31"),
    # ---- dependencias de la versión actual
    ("mas_pip_audit", "+ · pip-audit: vulnerabilidades conocidas en las dependencias (main)", "main",
     "pip-audit --progress-spinner off"),
    # ---- despliegue local con docker compose (main)
    ("dep_compose_build", "Despliegue · construcción de la imagen y arranque con docker compose", "main",
     "docker compose up -d --build --wait 2>&1 | tail -25"),
    ("dep_compose_ps", "Despliegue · contenedores en ejecución (aplicación y PostgreSQL 16)", "main",
     "docker compose ps && docker images trucha-smart-app"),
    ("dep_salud", "Despliegue · /api/salud y cabeceras de seguridad", "main",
     "curl -s http://localhost:8000/api/salud && echo && curl -s -D - -o /dev/null http://localhost:8000/login"),
    ("dep_bd", "Despliegue · PostgreSQL 16 con los datos cargados", "main",
     'docker compose exec -T db psql -U trucha -d truchasmart -c "SELECT version();" '
     '-c "SELECT count(*) AS lecturas FROM lecturas_agua;" -c "SELECT nombre_usuario, rol FROM usuarios ORDER BY id;"'),
    # ---- OWASP Top 10:2025 contra la app en Docker (main)
    *[(f"o_{a}", f"OWASP {a.upper()}:2025 contra la aplicación en Docker", "main",
       f"python tools/evidencias/owasp.py {a}") for a in ("a01", "a02", "a04", "a05", "a07", "a08", "a09", "a10")],
    # ---- WCAG con el árbol de accesibilidad (main)
    ("u_color", "U · WCAG 1.4.1: texto que acompaña a cada color de estado", "main", "python tools/evidencias/aria.py color"),
    ("u_aria_login", "U · WCAG 4.1.2: árbol de accesibilidad de /login", "main", "python tools/evidencias/aria.py login"),
    ("u_aria_panel", "U · WCAG 4.1.2 y 2.4.1: árbol de accesibilidad del panel", "main", "python tools/evidencias/aria.py panel"),
    ("dep_logs", "Despliegue · registro de peticiones del contenedor de la aplicación", "main",
     "docker compose logs app --tail 15"),
    # ---- despliegue público en Render (main)
    ("ren_test", "Render · pruebas automáticas del despliegue", "main",
     "python -m pytest tests/unit/test_despliegue.py -v -p no:warnings"),
    ("ren_salud", "Render · /api/salud del sitio público y cabeceras", "main",
     f"curl -sS -i --max-time 150 {RENDER}/api/salud"),
    ("ren_https", "Render · HTTP redirige a HTTPS y la cookie de sesión sale con Secure", "main",
     f"curl -sS -I http://truchasmart.onrender.com/login && curl -sS -o /dev/null -D - -X POST "
     f'{RENDER}/login -d "{LOGIN}" | grep -iE "^HTTP|set-cookie|location"'),
    ("ren_api", "Render · API REST pública: login JWT, panel y riesgo del modelo de IA", "main",
     "python tools/evidencias/render_api.py"),
]  # fmt: skip


def ejecutar(comando: str, cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    r = subprocess.run(
        ["bash", "-o", "pipefail", "-c", comando], cwd=cwd, env=env, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=1200,
    )  # fmt: skip
    salida = ANSI.sub("", (r.stdout + r.stderr).rstrip())
    return r.returncode, JWT.sub(lambda m: m.group(0)[:20] + "…(oculto)", salida)


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag-dir", type=Path, required=True, help="checkout del tag v3.0-Inc3")
    parser.add_argument("--tag-dir-1", type=Path, help="checkout del tag v1.0-PMV")
    parser.add_argument("--tag-dir-2", type=Path, help="checkout del tag v2.0-Inc2")
    parser.add_argument("--salida", type=Path, default=RAIZ / "evidencias" / "ejecuciones")
    parser.add_argument("--solo", nargs="*", help="nombres de evidencias a ejecutar")
    args = parser.parse_args(argv)
    args.salida.mkdir(parents=True, exist_ok=True)

    servidor, repo = (
        os.getenv("GITHUB_SERVER_URL", "https://github.com"),
        os.getenv("GITHUB_REPOSITORY", ""),
    )
    corrida, numero = os.getenv("GITHUB_RUN_ID", ""), os.getenv("GITHUB_RUN_NUMBER", "local")
    enlace = f"{servidor}/{repo}/actions/runs/{corrida}" if corrida else "(ejecución local)"
    dirs = {"tag": args.tag_dir, "tag1": args.tag_dir_1, "tag2": args.tag_dir_2}
    versiones = {
        clave: (
            d.resolve(),
            f"tag `{TAGS[clave]}` @ `{git('rev-parse', '--short', 'HEAD', cwd=d)}`",
        )
        for clave, d in dirs.items()
        if d
    }
    versiones["main"] = (RAIZ, f"rama `main` @ `{git('rev-parse', '--short', 'HEAD', cwd=RAIZ)}`")
    indice = []
    for nombre, titulo, donde, comando in EVIDENCIAS:
        if args.solo and nombre not in args.solo:
            continue
        if donde not in versiones:
            continue
        cwd, version = versiones[donde]
        for clave, (ruta, _) in versiones.items():  # {tag1}, {tag2}, {tag}: carpeta de cada tag
            comando = comando.replace("{" + clave + "}", str(ruta))
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "NO_COLOR": "1", "COLUMNS": "120"}
        if donde.startswith("tag"):
            env["PYTHONPATH"] = str(cwd)
        inicio = datetime.now(UTC)
        codigo, salida = ejecutar(comando, cwd, env)
        print(f"{'ok ' if codigo == 0 else 'ERR'} {nombre} ({codigo})", flush=True)
        (args.salida / f"{nombre}.md").write_text(
            f"# {titulo}\n\n"
            f"| Ejecución | Valor |\n|---|---|\n"
            f"| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #{numero} |\n"
            f"| Enlace | {enlace} |\n| Versión del código | {version} |\n"
            f"| Fecha (UTC) | {inicio:%d/%m/%Y %H:%M:%S} |\n| Código de salida | {codigo} |\n\n"
            f"```bash\n$ {comando}\n```\n\n```text\n{salida}\n```\n",
            encoding="utf-8",
        )
        indice.append(f"| [{nombre}]({nombre}.md) | {titulo} | {version} | {codigo} |")
    (args.salida / "README.md").write_text(
        "# Evidencias ejecutadas en GitHub Actions\n\n"
        f"Corrida #{numero} del workflow «Evidencias del informe»: {enlace}\n\n"
        "Cada página guarda el comando, su salida literal y el código de salida (0 = correcto). "
        "Las evidencias de calidad del producto se ejecutan sobre el tag v3.0-Inc3; las de despliegue "
        "y seguridad en ejecución, sobre main.\n\n"
        "| Evidencia | Qué verifica | Versión | Código de salida |\n|---|---|---|---|\n"
        + "\n".join(indice) + "\n",
        encoding="utf-8",
    )  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
