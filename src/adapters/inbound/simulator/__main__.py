"""Simulador de sensores: envía lecturas a POST /api/lecturas (ADR-004).

Uso:
    python -m src.adapters.inbound.simulator --estanque 1 --escenario normal --intervalo 5

Credenciales: --usuario/--password o variables SIM_USUARIO / SIM_PASSWORD
(por defecto el operario de los datos demo). Ctrl+C para detener.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx

from src.adapters.inbound.simulator.escenarios import ESCENARIOS, generar


def crear_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m src.adapters.inbound.simulator",
        description="Sensor simulado de calidad de agua para TruchaSmart",
    )
    p.add_argument("--estanque", type=int, required=True, help="id del estanque")
    p.add_argument("--escenario", choices=ESCENARIOS, default="normal")
    p.add_argument("--intervalo", type=float, default=5.0, help="segundos entre lecturas")
    p.add_argument("--cantidad", type=int, default=0, help="n.º de lecturas (0 = sin fin)")
    p.add_argument("--url", default=os.getenv("SIM_URL", "http://localhost:8000"))
    p.add_argument("--usuario", default=os.getenv("SIM_USUARIO", "operario"))
    p.add_argument("--password", default=os.getenv("SIM_PASSWORD", "Oper123!"))
    p.add_argument("--semilla", type=int, default=None, help="semilla aleatoria reproducible")
    return p


def ejecutar(args: argparse.Namespace, cliente: httpx.Client, dormir=time.sleep) -> int:
    """Autentica y envía lecturas. Devuelve el n.º de lecturas aceptadas."""
    r = cliente.post(
        "/api/auth/login", json={"nombre_usuario": args.usuario, "password": args.password}
    )
    if r.status_code != 200:
        print(f"Error de autenticación ({r.status_code}): {r.text}", file=sys.stderr)
        return 0
    cabeceras = {"Authorization": f"Bearer {r.json()['access_token']}"}
    aceptadas = 0
    for n, m in enumerate(generar(args.escenario, args.semilla), start=1):
        cuerpo = {
            "estanque_id": args.estanque,
            "temperatura_c": m.temperatura_c,
            "oxigeno_mg_l": m.oxigeno_mg_l,
            "ph": m.ph,
            "fuente": "SENSOR",
        }
        try:
            resp = cliente.post("/api/lecturas", json=cuerpo, headers=cabeceras)
        except httpx.HTTPError as e:
            print(f"[{n}] sin conexión con {args.url}: {e}", file=sys.stderr)
        else:
            if resp.status_code == 201:
                aceptadas += 1
                datos = resp.json()
                alertas = datos.get("alertas", [])
                extra = f" · {len(alertas)} alerta(s)" if alertas else ""
                print(
                    f"[{n}] estanque {args.estanque}: T={m.temperatura_c} °C, "
                    f"OD={m.oxigeno_mg_l} mg/L, pH={m.ph}{extra}"
                )
            else:
                print(f"[{n}] rechazada ({resp.status_code}): {resp.text}", file=sys.stderr)
        if args.cantidad and n >= args.cantidad:
            break
        dormir(args.intervalo)
    return aceptadas


def main(argv: list[str] | None = None) -> int:
    args = crear_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"Simulador → {args.url} · estanque {args.estanque} · escenario {args.escenario}")
    try:
        with httpx.Client(base_url=args.url, timeout=10) as cliente:
            ejecutar(args, cliente)
    except KeyboardInterrupt:
        print("\nSimulador detenido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
