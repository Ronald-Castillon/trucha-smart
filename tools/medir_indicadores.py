"""Mide los indicadores de valor TO-BE (IV-1, IV-2, IV-3) sobre la aplicación en ejecución.

Levanta la app (Uvicorn) de un checkout del repositorio sobre una SQLite temporal con
db/seed.sql y mide, sin estimar:

  IV-1  Tiempo desde que se registra una lectura CRÍTICA hasta que la alerta es visible en el
        panel web abierto (Playwright). Se repite --repeticiones veces y se reporta el máximo.
  IV-2  Tiempo para obtener el reporte mensual (calidad de agua y producción, PDF y CSV) por
        la API. Si la versión no tiene reportes (Inc. 1) queda en null.
  IV-3  Lecturas registradas por estanque y día: se ejecuta el simulador durante una ventana
        corta con el intervalo indicado y se cuenta lo que quedó en la BD; el resultado se
        extrapola a 24 h (se guarda la ventana real para que quede explícito).

Escribe docs/gqm/mediciones/medicion_<etiqueta>.json con las muestras crudas.

Uso:  python tools/medir_indicadores.py --etiqueta inc2
      python tools/medir_indicadores.py --etiqueta inc1 --repo ../trucha-v1   (checkout de v1.0-PMV)
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "gqm" / "mediciones"
USUARIOS = {"operario": "Oper123!", "piscicultor": "Pisci123!"}


def _puerto() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _token(api: httpx.Client, usuario: str) -> dict[str, str]:
    r = api.post("/api/auth/login", json={"nombre_usuario": usuario, "password": USUARIOS[usuario]})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def medir_iv1(url: str, repeticiones: int) -> dict:
    from playwright.sync_api import sync_playwright

    with httpx.Client(base_url=url, timeout=10) as api:
        pisc, oper = _token(api, "piscicultor"), _token(api, "operario")
        ids = [
            api.post("/api/estanques", json={"nombre": f"Medición IV-1 #{i}"}, headers=pisc).json()[
                "id"
            ]
            for i in range(repeticiones)
        ]
        muestras = []
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pag = nav.new_page(base_url=url)
            pag.goto("/login")
            pag.fill("input[name=nombre_usuario]", "operario")
            pag.fill("input[name=password]", USUARIOS["operario"])
            pag.click("button[type=submit]")
            pag.wait_for_url("**/panel")
            for eid in ids:
                inicio = time.perf_counter()
                api.post(
                    "/api/lecturas",
                    json={"estanque_id": eid, "temperatura_c": 12.5, "oxigeno_mg_l": 4.0,
                          "ph": 7.3},
                    headers=oper,
                ).raise_for_status()  # fmt: skip
                pag.locator(f'[data-estanque="{eid}"] .alerta .etiqueta.CRITICA').wait_for(
                    timeout=30000
                )
                muestras.append(round(time.perf_counter() - inicio, 3))
            nav.close()
    return {
        "descripcion": "lectura crítica (OD 4.0 mg/L) por API -> alerta CRÍTICA visible en el "
        "panel web abierto",
        "muestras_s": muestras,
        "promedio_s": round(sum(muestras) / len(muestras), 3),
        "maximo_s": max(muestras),
        "valor_minutos": round(max(muestras) / 60, 4),
        "criterio": "máximo de las muestras (peor caso observado)",
    }


def medir_iv2(url: str) -> dict:
    with httpx.Client(base_url=url, timeout=60) as api:
        pisc = _token(api, "piscicultor")
        rutas = [
            f"/api/reportes/{tipo}.{fmt}?desde=2026-10-01&hasta=2026-10-31"
            for tipo in ("calidad-agua", "produccion")
            for fmt in ("pdf", "csv")
        ]
        inicio = time.perf_counter()
        detalle = []
        for ruta in rutas:
            r = api.get(ruta, headers=pisc)
            if r.status_code == 404:
                return {"descripcion": "la versión no tiene exportación de reportes",
                        "valor_horas": None}  # fmt: skip
            r.raise_for_status()
            detalle.append({"ruta": ruta, "bytes": len(r.content)})
        segundos = round(time.perf_counter() - inicio, 3)
    return {
        "descripcion": "obtener el reporte mensual (octubre 2026): calidad de agua y producción "
        "en PDF y CSV por la API",
        "archivos": detalle,
        "segundos": segundos,
        "valor_horas": round(segundos / 3600, 6),
    }


def medir_iv3(url: str, repo: Path, env: dict, intervalo: float, cantidad: int) -> dict:
    with httpx.Client(base_url=url, timeout=10) as api:
        pisc = _token(api, "piscicultor")
        eid = api.post("/api/estanques", json={"nombre": "Medición IV-3"}, headers=pisc).json()[
            "id"
        ]
        inicio = time.perf_counter()
        subprocess.run(
            [sys.executable, "-m", "src.adapters.inbound.simulator", "--estanque", str(eid),
             "--escenario", "normal", "--intervalo", str(intervalo), "--cantidad", str(cantidad),
             "--url", url],
            cwd=repo, env=env, check=True, capture_output=True,
        )  # fmt: skip
        ventana = time.perf_counter() - inicio
        oper = _token(api, "operario")
        registradas = len(
            api.get(f"/api/lecturas?estanque_id={eid}&limite=500", headers=oper).json()
        )
    por_dia = registradas / ventana * 86400
    return {
        "descripcion": f"simulador escenario normal con --intervalo {intervalo:g} s; lecturas "
        "registradas en la BD durante la ventana, extrapoladas a 24 h",
        "lecturas_registradas": registradas,
        "ventana_s": round(ventana, 3),
        "valor_lecturas_dia": round(por_dia, 1),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Medición TO-BE de IV-1..IV-3")
    parser.add_argument("--etiqueta", required=True, help="p. ej. inc1, inc2")
    parser.add_argument("--repo", type=Path, default=RAIZ, help="checkout a medir")
    parser.add_argument("--repeticiones", type=int, default=5)
    parser.add_argument("--intervalo", type=float, default=5.0)
    parser.add_argument("--cantidad", type=int, default=7)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    repo = args.repo.resolve()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        bd = f"sqlite:///{Path(tmp, 'medicion.db').as_posix()}"
        env = {**os.environ, "DATABASE_URL": bd, "JWT_SECRET": "medicion-indicadores-32-bytes-min!",
               "PYTHONIOENCODING": "utf-8"}  # fmt: skip
        subprocess.run([sys.executable, "tools/init_db.py", "--url", bd], cwd=repo, env=env,
                       check=True, capture_output=True)  # fmt: skip
        puerto = _puerto()
        url = f"http://127.0.0.1:{puerto}"
        servidor = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.main:app", "--port", str(puerto)],
            cwd=repo, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )  # fmt: skip
        try:
            for _ in range(100):
                try:
                    if httpx.get(f"{url}/api/salud", timeout=0.5).status_code == 200:
                        break
                except httpx.HTTPError:
                    time.sleep(0.1)
            version = subprocess.run(
                ["git", "describe", "--tags", "--always"], cwd=repo, capture_output=True,
                text=True,
            ).stdout.strip()  # fmt: skip
            resultado = {
                "etiqueta": args.etiqueta,
                "version_medida": version,
                "medido_en": datetime.now(UTC).isoformat(timespec="seconds"),
                "entorno": f"{sys.platform}, Python {sys.version.split()[0]}, SQLite, Chromium "
                "headless (Playwright)",
                "IV-1": medir_iv1(url, args.repeticiones),
                "IV-2": medir_iv2(url),
                "IV-3": medir_iv3(url, repo, env, args.intervalo, args.cantidad),
            }
        finally:
            servidor.terminate()
            servidor.wait(timeout=10)

    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / f"medicion_{args.etiqueta}.json"
    destino.write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f"Escrito {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
