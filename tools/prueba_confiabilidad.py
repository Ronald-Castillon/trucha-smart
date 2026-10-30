"""RNF-R: prueba de confiabilidad por inyección de fallos (caos) con medición real.

1. Un *supervisor* arranca la API con uvicorn y la reinicia apenas termina (como la política
   `restart: always` de docker-compose o `Restart=always` de systemd).
2. Un *inyector de fallos* mata el proceso del servidor (`kill`) N veces durante la prueba.
3. Una *sonda* consulta `GET /api/salud` cada 250 ms durante toda la prueba.
4. Opcional (`--pg-contenedor`): detiene y vuelve a iniciar el contenedor de PostgreSQL y mide si
   la API sigue respondiendo (503) durante la caída y cuánto tarda en volver a 200 (reconexión).

Métricas (sobre las muestras de la sonda):
  Disponibilidad = (duración - tiempo caído) / duración x 100, con tiempo caído = suma de los
    tiempos de recuperación (por tiempo y no por número de sondas: en Windows una sonda a un
    puerto cerrado tarda 1-2 s en fallar, y contar sondas subestimaría la caída)
  MTTR = promedio de (primer 200 tras el fallo - instante del fallo)
  MTBF = tiempo en servicio / número de fallos

Uso:
  python tools/prueba_confiabilidad.py --duracion 300 --fallos 5
  python tools/prueba_confiabilidad.py --url-bd postgresql+psycopg://... --pg-contenedor ID
Guarda docs/calidad/confiabilidad.json y .md (o --salida).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parents[1]
DISPONIBILIDAD_META = 99.5  # %, umbral de la guía S10
MTTR_META_S = 300.0  # < 5 min


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Supervisor(threading.Thread):
    """Mantiene el servidor vivo: si el proceso termina, lo vuelve a lanzar."""

    def __init__(self, puerto: int, env: dict) -> None:
        super().__init__(daemon=True)
        self.puerto, self.env = puerto, env
        self.proceso: subprocess.Popen | None = None
        self.reinicios = 0
        self.activo = True
        self._listo = threading.Event()

    def _lanzar(self) -> None:
        self.proceso = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.main:app", "--port", str(self.puerto)],
            cwd=RAIZ,
            env=self.env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def run(self) -> None:
        self._lanzar()
        self._listo.set()
        while self.activo:
            if self.proceso.poll() is not None and self.activo:
                self.reinicios += 1
                self._lanzar()
            time.sleep(0.05)

    def matar(self) -> None:
        self._listo.wait()
        self.proceso.kill()

    def detener(self) -> None:
        self.activo = False
        if self.proceso and self.proceso.poll() is None:
            self.proceso.terminate()
            self.proceso.wait(timeout=10)


class Sonda(threading.Thread):
    def __init__(self, url: str, intervalo: float) -> None:
        super().__init__(daemon=True)
        self.url, self.intervalo = url, intervalo
        # (instante de la respuesta, código HTTP o 0 si no conecta). Se usa el instante en que llega
        # la respuesta: en Windows la conexión al puerto caído espera a que el servidor reinicie.
        self.muestras: list[tuple[float, int]] = []
        self.activo = True

    def run(self) -> None:
        with httpx.Client(timeout=4.0) as cliente:  # > connect_timeout de la BD (3 s)
            while self.activo:
                t = time.monotonic()
                try:
                    codigo = cliente.get(f"{self.url}/api/salud").status_code
                except httpx.HTTPError:
                    codigo = 0
                self.muestras.append((time.monotonic(), codigo))
                time.sleep(max(0.0, self.intervalo - (time.monotonic() - t)))


def esperar_200(url: str, limite_s: float = 60) -> None:
    fin = time.monotonic() + limite_s
    while time.monotonic() < fin:
        try:
            if httpx.get(f"{url}/api/salud", timeout=0.5).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    raise SystemExit("La API no respondió 200 al iniciar la prueba")


def recuperacion(muestras, instante: float) -> float | None:
    """Segundos desde `instante` hasta la primera sonda con 200 posterior."""
    return next((t - instante for t, c in muestras if t > instante and c == 200), None)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--duracion", type=float, default=300, help="segundos de prueba (def. 300)")
    ap.add_argument("--fallos", type=int, default=5, help="veces que se mata el servidor")
    ap.add_argument("--intervalo", type=float, default=0.25, help="segundos entre sondas")
    ap.add_argument("--url-bd", help="DATABASE_URL (por defecto, SQLite temporal con datos demo)")
    ap.add_argument("--pg-contenedor", help="contenedor Docker de PostgreSQL para la caída de BD")
    ap.add_argument("--pg-caida", type=float, default=10, help="segundos con PostgreSQL detenido")
    ap.add_argument("--salida", default=str(RAIZ / "docs/calidad/confiabilidad"))
    ap.add_argument("--semilla", type=int, default=10)
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    random.seed(args.semilla)

    url_bd = args.url_bd or f"sqlite:///{Path(tempfile.mkdtemp()).as_posix()}/caos.db"
    env = {
        **os.environ,
        "DATABASE_URL": url_bd,
        "JWT_SECRET": os.environ.get("JWT_SECRET", "clave-de-prueba-de-confiabilidad-32b!"),
        "PYTHONIOENCODING": "utf-8",
    }
    subprocess.run(
        [sys.executable, "tools/init_db.py", "--url", url_bd], cwd=RAIZ, env=env, check=True
    )
    puerto = puerto_libre()
    url = f"http://127.0.0.1:{puerto}"
    supervisor = Supervisor(puerto, env)
    supervisor.start()
    esperar_200(url)

    sonda = Sonda(url, args.intervalo)
    inicio = time.monotonic()
    sonda.start()
    # Fallos repartidos en la ventana central, con separación mínima para medir cada recuperación.
    tramo = args.duracion / (args.fallos + 1)
    momentos = [tramo * (i + 1) + random.uniform(-tramo / 4, tramo / 4) for i in range(args.fallos)]
    fallos: list[float] = []
    for m in momentos:
        time.sleep(max(0.0, inicio + m - time.monotonic()))
        fallos.append(time.monotonic())
        supervisor.matar()
        print(f"  fallo inyectado en t={fallos[-1] - inicio:6.1f} s (kill del servidor)")

    caida_bd = None
    if args.pg_contenedor:
        time.sleep(5)
        t0 = time.monotonic()
        subprocess.run(["docker", "stop", args.pg_contenedor], check=True, capture_output=True)
        print(f"  PostgreSQL detenido en t={t0 - inicio:6.1f} s")
        time.sleep(args.pg_caida)
        t_inicio_pg = time.monotonic()
        subprocess.run(["docker", "start", args.pg_contenedor], check=True, capture_output=True)
        durante = [c for t, c in sonda.muestras if t0 + 1 < t < t_inicio_pg]
        espera = recuperacion_bloqueante(sonda, t_inicio_pg)
        caida_bd = {
            "segundos_detenido": round(t_inicio_pg - t0, 1),
            "respuestas_durante_caida": {str(c): durante.count(c) for c in sorted(set(durante))},
            "api_siguio_respondiendo": bool(durante) and all(c == 503 for c in durante),
            "reconexion_s_desde_docker_start": espera,
        }

    time.sleep(max(0.0, inicio + args.duracion - time.monotonic()))
    sonda.activo = False
    sonda.join()
    supervisor.detener()

    muestras = sonda.muestras
    total = len(muestras)
    ok = sum(1 for _, c in muestras if c == 200)
    tr = [recuperacion(muestras, f) for f in fallos]
    tr_validos = [x for x in tr if x is not None]
    duracion = muestras[-1][0] - muestras[0][0]
    caido = sum(tr_validos)
    resultado = {
        "ejecutado_en": datetime.now(UTC).isoformat(timespec="seconds"),
        "entorno": {
            "so": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "base_de_datos": url_bd.split(":")[0],
            "nucleos_cpu": os.cpu_count(),
        },
        "parametros": {
            "duracion_s": args.duracion,
            "fallos_inyectados": len(fallos),
            "intervalo_sonda_s": args.intervalo,
        },
        "sondas": {"total": total, "con_200": ok, "sin_respuesta_o_error": total - ok},
        "disponibilidad_pct": round(100 * (duracion - caido) / duracion, 3),
        "sondas_200_pct": round(100 * ok / total, 3),
        "tiempos_recuperacion_s": [round(x, 2) if x is not None else None for x in tr],
        "mttr_s": round(statistics.mean(tr_validos), 2) if tr_validos else None,
        "mtbf_s": round((duracion - caido) / len(fallos), 1) if fallos else None,
        "reinicios_del_supervisor": supervisor.reinicios,
        "caida_postgresql": caida_bd,
        "metas": {"disponibilidad_pct": DISPONIBILIDAD_META, "mttr_s": MTTR_META_S},
    }
    resultado["fallos_tolerables_dia"] = (
        int(86400 * (1 - DISPONIBILIDAD_META / 100) / resultado["mttr_s"])
        if resultado["mttr_s"]
        else None
    )
    resultado["cumple"] = {
        "disponibilidad": resultado["disponibilidad_pct"] >= DISPONIBILIDAD_META,
        "mttr": resultado["mttr_s"] is not None and resultado["mttr_s"] < MTTR_META_S,
    }
    guardar(resultado, Path(args.salida))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


def recuperacion_bloqueante(sonda: Sonda, desde: float, limite_s: float = 120) -> float | None:
    fin = time.monotonic() + limite_s
    while time.monotonic() < fin:
        r = recuperacion(list(sonda.muestras), desde)
        if r is not None:
            return round(r, 2)
        time.sleep(0.2)
    return None


def guardar(r: dict, base: Path) -> None:
    base.parent.mkdir(parents=True, exist_ok=True)
    base.with_suffix(".json").write_text(json.dumps(r, ensure_ascii=False, indent=2), "utf-8")
    si = {True: "Sí", False: "No"}
    lineas = [
        "# Prueba de confiabilidad (RNF-R) — resultado medido",
        "",
        f"Generado por `tools/prueba_confiabilidad.py` el {r['ejecutado_en']} "
        f"({r['entorno']['so']}, Python {r['entorno']['python']}, "
        f"BD {r['entorno']['base_de_datos']}).",
        "",
        "| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |",
        "|---|---:|---:|:---:|",
        f"| Disponibilidad (1 - tiempo caído / duración) | {r['disponibilidad_pct']} % "
        f"| ≥ {r['metas']['disponibilidad_pct']} % | {si[r['cumple']['disponibilidad']]} |",
        f"| MTTR (fallo → primer 200) | {r['mttr_s']} s | < {int(r['metas']['mttr_s'])} s "
        f"| {si[r['cumple']['mttr']]} |",
        f"| MTBF (tiempo en servicio / fallos) | {r['mtbf_s']} s | — | — |",
        "",
        f"- Duración: {r['parametros']['duracion_s']} s; fallos inyectados (kill del proceso): "
        f"{r['parametros']['fallos_inyectados']}; reinicios del supervisor: "
        f"{r['reinicios_del_supervisor']}.",
        f"- Sondas `GET /api/salud` cada {r['parametros']['intervalo_sonda_s']} s: "
        f"{r['sondas']['total']} en total, {r['sondas']['con_200']} con 200 "
        f"({r['sondas_200_pct']} %; métrica secundaria, ver nota en el código).",
        f"- Tiempo de recuperación de cada fallo (s): {r['tiempos_recuperacion_s']}.",
    ]
    if r["caida_postgresql"]:
        c = r["caida_postgresql"]
        lineas += [
            "",
            "## Caída de PostgreSQL",
            "",
            f"- PostgreSQL detenido {c['segundos_detenido']} s; respuestas de `/api/salud` durante "
            f"la caída: {c['respuestas_durante_caida']} (la API "
            f"{'siguió respondiendo 503, sin caerse' if c['api_siguio_respondiendo'] else 'NO'}).",
            f"- Reconexión automática (pool_pre_ping): primer 200 a los "
            f"{c['reconexion_s_desde_docker_start']} s de `docker start` "
            "(incluye el arranque de PostgreSQL).",
        ]
    lineas += [
        "",
        "## Interpretación",
        "",
        f"La prueba fuerza **un fallo cada {r['mtbf_s']} s** aprox., una tasa mucho mayor que la",
        "real, para medir la recuperación. En régimen estable la disponibilidad es",
        "A = MTBF / (MTBF + MTTR); con el MTTR medido, la meta de 99.5 % (432 s de caída al día)",
        f"se mantiene con hasta **{r['fallos_tolerables_dia']} caídas del proceso por día**.",
        "",
        "**Alcance:** recuperación ante caídas del proceso y de la BD en un servidor con",
        "supervisor; no reemplaza una medición de disponibilidad en producción durante meses.",
        "",
    ]
    base.with_suffix(".md").write_text("\n".join(lineas), "utf-8")


if __name__ == "__main__":
    sys.exit(main())
