"""RNF-P: prueba de carga con Locust y medición real de latencia, throughput y memoria.

Arranca la API (uvicorn, N workers) sobre una BD con datos demo, ejecuta Locust sin interfaz con
`tests/carga/locustfile.py` y muestrea cada segundo la memoria (RSS) y CPU del servidor con psutil.

Métricas (fila "Aggregated" de Locust):
  p95 = percentil 95 del tiempo de respuesta (ms)
  RPS = peticiones por segundo atendidas
  Errores = peticiones fallidas / peticiones totales x 100

Uso:
  python tools/prueba_carga.py --usuarios 500 --tasa 25 --duracion 180 --workers 4
  python tools/prueba_carga.py --url-bd postgresql+psycopg://... (en CI)
Guarda docs/calidad/rendimiento.json y .md (o --salida).
"""

from __future__ import annotations

import argparse
import csv
import json
import locale
import math
import os
import platform
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import psutil

RAIZ = Path(__file__).resolve().parents[1]
P95_META_MS = 800  # guía S10: p95 < 800 ms con 500 usuarios
ERRORES_META_PCT = 1.0


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Monitor(threading.Thread):
    """Muestrea RSS (MB) y CPU (%) del proceso servidor y sus hijos (workers)."""

    def __init__(self, pid: int) -> None:
        super().__init__(daemon=True)
        self.proceso = psutil.Process(pid)
        self.memoria_mb: list[float] = []
        self.cpu_pct: list[float] = []
        self.activo = True

        self._cache: dict[int, psutil.Process] = {}

    def _procesos(self):
        # Se reutilizan los objetos Process: cpu_percent() mide desde la llamada anterior.
        actuales = [self.proceso, *self.proceso.children(recursive=True)]
        return [self._cache.setdefault(p.pid, p) for p in actuales]

    def run(self) -> None:
        for p in self._procesos():
            p.cpu_percent(None)
        while self.activo:
            time.sleep(1)
            try:
                procs = self._procesos()
                self.memoria_mb.append(sum(p.memory_info().rss for p in procs) / 2**20)
                self.cpu_pct.append(sum(p.cpu_percent(None) for p in procs))
            except psutil.Error:
                pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--usuarios", type=int, default=500)
    ap.add_argument("--tasa", type=float, default=25, help="usuarios nuevos por segundo")
    ap.add_argument("--duracion", type=int, default=180, help="segundos de carga")
    ap.add_argument("--workers", type=int, default=4, help="procesos uvicorn")
    ap.add_argument("--url-bd", help="DATABASE_URL (por defecto, SQLite temporal con datos demo)")
    ap.add_argument("--salida", default=str(RAIZ / "docs/calidad/rendimiento"))
    ap.add_argument("--log-servidor", help="archivo donde guardar la salida del servidor")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    tmp = Path(tempfile.mkdtemp())
    url_bd = args.url_bd or f"sqlite:///{tmp.as_posix()}/carga.db"
    env = {
        **os.environ,
        "DATABASE_URL": url_bd,
        "JWT_SECRET": os.environ.get("JWT_SECRET", "clave-de-prueba-de-carga-de-32-bytes!"),
        "PYTHONIOENCODING": "utf-8",
    }
    subprocess.run(
        [sys.executable, "tools/init_db.py", "--url", url_bd], cwd=RAIZ, env=env, check=True
    )
    puerto = puerto_libre()
    host = f"http://127.0.0.1:{puerto}"
    log = (
        open(args.log_servidor, "w", encoding="utf-8") if args.log_servidor else subprocess.DEVNULL
    )
    servidor = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--port", str(puerto),
         "--workers", str(args.workers), "--log-level", "warning"],
        cwd=RAIZ, env=env, stdout=log, stderr=subprocess.STDOUT,
    )  # fmt: skip
    try:
        for _ in range(200):
            try:
                if httpx.get(f"{host}/api/salud", timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        else:
            raise SystemExit("La API no arrancó")
        monitor = Monitor(servidor.pid)
        monitor.start()
        prefijo = tmp / "locust"
        env["LOCUST_MUESTRAS"] = str(tmp / "muestras.csv")
        inicio = time.monotonic()
        subprocess.run(
            [sys.executable, "-m", "locust", "-f", "tests/carga/locustfile.py", "--headless",
             "--host", host, "-u", str(args.usuarios), "-r", str(args.tasa),
             "-t", f"{args.duracion}s", "--csv", str(prefijo), "--only-summary"],
            cwd=RAIZ, env=env, check=False,
        )  # fmt: skip
        segundos = time.monotonic() - inicio
        monitor.activo = False
        monitor.join()
    finally:
        servidor.terminate()
        servidor.wait(timeout=15)

    filas = list(csv.DictReader(open(f"{prefijo}_stats.csv", encoding="utf-8")))
    agregada = next(f for f in filas if f["Name"] == "Aggregated")
    por_endpoint = [
        {
            "endpoint": f["Name"],
            "peticiones": int(f["Request Count"]),
            "fallos": int(f["Failure Count"]),
            "mediana_ms": float(f["50%"]),
            "p95_ms": float(f["95%"]),
            "p99_ms": float(f["99%"]),
            "rps": round(float(f["Requests/s"]), 1),
        }
        for f in filas
        if f["Name"] != "Aggregated"
    ]
    fases = fases_de(tmp / "muestras.csv", args.usuarios / args.tasa)
    errores = [
        {"endpoint": f["Name"], "error": f["Error"][:200], "veces": int(f["Occurrences"])}
        for f in csv.DictReader(
            open(
                f"{prefijo}_failures.csv",
                encoding=locale.getpreferredencoding(False),
                errors="replace",
            )
        )
    ]
    total, fallos = int(agregada["Request Count"]), int(agregada["Failure Count"])
    r = {
        "ejecutado_en": datetime.now(UTC).isoformat(timespec="seconds"),
        "entorno": {
            "so": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "nucleos_cpu": os.cpu_count(),
            "memoria_total_gb": round(psutil.virtual_memory().total / 2**30, 1),
            "base_de_datos": url_bd.split(":")[0],
            "workers_uvicorn": args.workers,
            "nota": "Locust y la API se ejecutan en la misma máquina y comparten CPU.",
        },
        "parametros": {
            "usuarios": args.usuarios,
            "tasa_usuarios_s": args.tasa,
            "duracion_s": args.duracion,
            "escenario": "tests/carga/locustfile.py (90 % consulta, 10 % sensores)",
        },
        "peticiones": total,
        "fallos": fallos,
        "errores_pct": round(100 * fallos / total, 3) if total else None,
        "p50_ms": float(agregada["50%"]),
        "p95_ms": float(agregada["95%"]),
        "p99_ms": float(agregada["99%"]),
        "rps": round(float(agregada["Requests/s"]), 1),
        "memoria_servidor_mb": {
            "promedio": round(sum(monitor.memoria_mb) / len(monitor.memoria_mb), 1),
            "maxima": round(max(monitor.memoria_mb), 1),
        },
        "cpu_servidor_pct_max": round(max(monitor.cpu_pct), 1),
        "duracion_real_s": round(segundos, 1),
        "fases": fases,
        "por_endpoint": por_endpoint,
        "errores": sorted(errores, key=lambda x: -x["veces"])[:10],
        "metas": {"p95_ms": P95_META_MS, "errores_pct": ERRORES_META_PCT},
    }
    estable = fases.get("estable") or {}
    r["cumple"] = {
        "p95": r["p95_ms"] < P95_META_MS,
        "p95_estable": bool(estable) and estable["p95_ms"] < P95_META_MS,
        "errores": r["errores_pct"] is not None and r["errores_pct"] < ERRORES_META_PCT,
    }
    guardar(r, Path(args.salida))
    print(json.dumps({k: v for k, v in r.items() if k != "por_endpoint"}, ensure_ascii=False,
                     indent=2))  # fmt: skip
    return 0


def percentil(valores: list[float], q: float) -> float:
    """Percentil por rango más cercano (el mismo criterio que usa Locust, sin redondeo)."""
    orden = sorted(valores)
    return orden[max(0, math.ceil(q / 100 * len(orden)) - 1)]


def fases_de(ruta: Path, rampa_s: float) -> dict:
    """Separa la rampa de subida (usuarios entrando y autenticándose) del estado estable."""
    if not ruta.is_file():
        return {}
    filas = [(float(t), float(ms), n, int(ok)) for t, ms, n, ok in csv.reader(open(ruta))]
    if not filas:
        return {}
    inicio = min(f[0] for f in filas)
    resultado = {}
    for nombre, cond in (
        ("rampa", lambda t: t - inicio < rampa_s),
        ("estable", lambda t: t - inicio >= rampa_s),
    ):
        sel = [f for f in filas if cond(f[0])]
        if not sel:
            continue
        ms = [f[1] for f in sel]
        dur = max(f[0] for f in sel) - min(f[0] for f in sel) or 1
        resultado[nombre] = {
            "segundos": round(dur, 1),
            "peticiones": len(sel),
            "p50_ms": round(percentil(ms, 50)),
            "p95_ms": round(percentil(ms, 95)),
            "p99_ms": round(percentil(ms, 99)),
            "errores_pct": round(100 * sum(1 for f in sel if not f[3]) / len(sel), 3),
            "rps": round(len(sel) / dur, 1),
        }
    return resultado


def guardar(r: dict, base: Path) -> None:
    base.parent.mkdir(parents=True, exist_ok=True)
    base.with_suffix(".json").write_text(json.dumps(r, ensure_ascii=False, indent=2), "utf-8")
    si = {True: "Sí", False: "No"}
    e, p = r["entorno"], r["parametros"]
    lineas = [
        "# Prueba de carga (RNF-P) — resultado medido",
        "",
        f"Generado por `tools/prueba_carga.py` el {r['ejecutado_en']} con Locust "
        f"({e['so']}, {e['nucleos_cpu']} núcleos, {e['memoria_total_gb']} GB, BD "
        f"{e['base_de_datos']}, {e['workers_uvicorn']} workers uvicorn). {e['nota']}",
        "",
        f"Carga: **{p['usuarios']} usuarios concurrentes** (rampa {p['tasa_usuarios_s']}/s) "
        "durante "
        f"{p['duracion_s']} s; escenario {p['escenario']}.",
        "",
        "| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |",
        "|---|---:|---:|:---:|",
        f"| Latencia p95 | {r['p95_ms']:.0f} ms | < {r['metas']['p95_ms']} ms "
        f"| {si[r['cumple']['p95']]} |",
        f"| Tasa de errores | {r['errores_pct']} % | < {r['metas']['errores_pct']} % "
        f"| {si[r['cumple']['errores']]} |",
        f"| Throughput | {r['rps']} RPS | — | — |",
        f"| Latencia p50 / p99 | {r['p50_ms']:.0f} / {r['p99_ms']:.0f} ms | — | — |",
        f"| Memoria del servidor (promedio / máx.) | {r['memoria_servidor_mb']['promedio']} / "
        f"{r['memoria_servidor_mb']['maxima']} MB | — | — |",
        f"| CPU del servidor (máx., suma de workers) | {r['cpu_servidor_pct_max']} % | — | — |",
        "",
        f"Peticiones: {r['peticiones']} ({r['fallos']} fallidas).",
        "",
        "Por fase (muestras crudas de cada petición; la rampa incluye el inicio de sesión de",
        "los usuarios, que usa bcrypt y es intensivo en CPU por diseño):",
        "",
        "| Fase | Duración | Peticiones | p50 ms | p95 ms | p99 ms | Errores | RPS | p95 < meta |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|",
        *[
            f"| {nombre} | {f['segundos']} s | {f['peticiones']} | {f['p50_ms']} | {f['p95_ms']} "
            f"| {f['p99_ms']} | {f['errores_pct']} % | {f['rps']} "
            f"| {si[f['p95_ms'] < r['metas']['p95_ms']]} |"
            for nombre, f in r["fases"].items()
        ],
        "",
        "| Endpoint | Peticiones | Fallos | p50 ms | p95 ms | p99 ms | RPS |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *[
            f"| `{x['endpoint']}` | {x['peticiones']} | {x['fallos']} | {x['mediana_ms']:.0f} "
            f"| {x['p95_ms']:.0f} | {x['p99_ms']:.0f} | {x['rps']} |"
            for x in r["por_endpoint"]
        ],
        "",
        "Errores registrados por Locust (los más frecuentes):",
        "",
        *[f"- `{x['endpoint']}` × {x['veces']}: {x['error']}" for x in r["errores"]],
        "",
    ]
    base.with_suffix(".md").write_text("\n".join(lineas), "utf-8")


if __name__ == "__main__":
    sys.exit(main())
