"""Infraestructura E2E: levanta la app con Uvicorn sobre una SQLite temporal y abre Chromium.

Todas las pruebas de esta carpeta se marcan como `e2e` (se ejecutan con `pytest -m e2e`).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "evidencias"


def pytest_collection_modifyitems(items):
    for item in items:
        if Path(str(item.fspath)).is_relative_to(Path(__file__).parent):
            item.add_marker(pytest.mark.e2e)


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def url_base(tmp_path_factory) -> Iterator[str]:
    bd = tmp_path_factory.mktemp("e2e") / "e2e.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{bd.as_posix()}", "JWT_SECRET": "e2e"}
    subprocess.run(
        [sys.executable, "tools/init_db.py", "--url", env["DATABASE_URL"]],
        cwd=RAIZ,
        env=env,
        check=True,
    )
    puerto = _puerto_libre()
    proceso = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--port", str(puerto)],
        cwd=RAIZ,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{puerto}"
    for _ in range(100):
        try:
            if httpx.get(f"{url}/api/salud", timeout=0.5).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.1)
    else:
        proceso.kill()
        pytest.fail("La aplicación no arrancó para las pruebas E2E")
    yield url
    proceso.terminate()
    proceso.wait(timeout=10)


@pytest.fixture(scope="session")
def navegador():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        nav = p.chromium.launch()
        yield nav
        nav.close()


@pytest.fixture
def pagina(navegador, url_base):
    contexto = navegador.new_context(base_url=url_base, viewport={"width": 1280, "height": 800})
    pag = contexto.new_page()
    yield pag
    contexto.close()


def capturar(pagina, incremento: int, rf: int, paso: int) -> Path:
    """Guarda evidencias/incN/RF0X_paso1_entrada.png o RF0X_paso2_resultado.png."""
    sufijo = {1: "entrada", 2: "resultado"}[paso]
    destino = EVIDENCIAS / f"inc{incremento}" / f"RF{rf:02d}_paso{paso}_{sufijo}.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    pagina.screenshot(path=str(destino), full_page=True)
    return destino
