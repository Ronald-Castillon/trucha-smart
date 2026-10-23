"""Genera db/seed.sql con datos de demostración reproducibles.

- 3 usuarios (uno por rol) con contraseña hasheada con bcrypt.
- 3 estanques/jaulas con un lote activo cada uno.
- Lecturas cada 3 horas durante 7 días (2026-10-16 a 2026-10-22, UTC).
- La jaula J1 tiene dos caídas de oxígeno a nivel de PRECAUCIÓN con su alerta
  (una atendida y otra abierta), coherentes con config/umbrales.yaml.
- Alimentación diaria y algunos registros de mortalidad.

Uso:  python tools/generar_seed.py
Las contraseñas de demostración están documentadas en el README.
"""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import bcrypt

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "db" / "seed.sql"

# Sal fija para que el archivo generado sea reproducible (solo datos de demostración).
SAL_DEMO = b"$2b$12$TruchaSmartDemoSaltSee"

USUARIOS = [
    (1, "admin", "Ana Administradora", "Admin123!", "ADMINISTRADOR"),
    (2, "piscicultor", "Pedro Piscicultor", "Pisci123!", "PISCICULTOR"),
    (3, "operario", "Olga Operaria", "Oper123!", "OPERARIO"),
]
ESTANQUES = [
    (1, "Estanque A1", "ESTANQUE", 120.0, "Sector norte"),
    (2, "Estanque A2", "ESTANQUE", 120.0, "Sector norte"),
    (3, "Jaula J1", "JAULA", 250.0, "Laguna, muelle 2"),
]
# id, estanque, código, peces, peso inicial, peso actual, siembra
LOTES = [
    (1, 1, "L-2026-01", 5000, 45.0, 62.0, "2026-08-01"),
    (2, 2, "L-2026-02", 8000, 8.0, 15.0, "2026-09-10"),
    (3, 3, "L-2026-03", 3000, 180.0, 230.0, "2026-06-15"),
]
INICIO = datetime(2026, 10, 16, 0, 0, tzinfo=UTC)
DIAS = 7
PASO_HORAS = 3

# Ventanas (inicio, fin) en las que la jaula J1 tiene OD en precaución (5.0 <= OD < 7.0).
CAIDAS_OD_J1 = [
    (INICIO + timedelta(days=2, hours=3), INICIO + timedelta(days=2, hours=9)),
    (INICIO + timedelta(days=6, hours=12), INICIO + timedelta(days=6, hours=21)),
]


def ts(d: datetime) -> str:
    return d.strftime("'%Y-%m-%d %H:%M:%S+00'")


def generar() -> str:
    rnd = random.Random(20261023)
    out: list[str] = [
        "-- Generado por tools/generar_seed.py. No editar a mano: regenerar.",
        "-- Datos de demostración (contraseñas en el README).",
        "",
    ]

    out.append(
        "INSERT INTO usuarios (id, nombre_usuario, nombre_completo, password_hash, rol, activo, "
        "creado_en) VALUES"
    )
    filas = []
    for uid, user, nombre, pwd, rol in USUARIOS:
        h = bcrypt.hashpw(pwd.encode(), SAL_DEMO).decode()
        filas.append(f"  ({uid}, '{user}', '{nombre}', '{h}', '{rol}', TRUE, {ts(INICIO)})")
    out.append(",\n".join(filas) + ";\n")

    out.append(
        "INSERT INTO estanques (id, nombre, tipo, volumen_m3, ubicacion, activo, creado_en) VALUES"
    )
    out.append(
        ",\n".join(
            f"  ({e[0]}, '{e[1]}', '{e[2]}', {e[3]:.2f}, '{e[4]}', TRUE, {ts(INICIO)})"
            for e in ESTANQUES
        )
        + ";\n"
    )

    out.append(
        "INSERT INTO lotes (id, estanque_id, codigo, num_peces_inicial, peso_medio_inicial_g, "
        "peso_medio_actual_g, fecha_siembra, activo, fecha_cierre) VALUES"
    )
    out.append(
        ",\n".join(
            f"  ({lo[0]}, {lo[1]}, '{lo[2]}', {lo[3]}, {lo[4]:.2f}, {lo[5]:.2f}, '{lo[6]}', "
            "TRUE, NULL)"
            for lo in LOTES
        )
        + ";\n"
    )

    lecturas = []
    alertas = []
    lid = 0
    for est_id, *_ in ESTANQUES:
        alerta_abierta: dict | None = None
        t = INICIO
        while t < INICIO + timedelta(days=DIAS):
            lid += 1
            hora = t.hour + t.minute / 60
            temp = 12.5 + 1.8 * math.sin((hora - 9) / 24 * 2 * math.pi) + rnd.uniform(-0.3, 0.3)
            od = 8.4 - 0.5 * math.sin((hora - 9) / 24 * 2 * math.pi) + rnd.uniform(-0.3, 0.3)
            ph = 7.3 + rnd.uniform(-0.25, 0.25)
            en_caida = est_id == 3 and any(a <= t <= b for a, b in CAIDAS_OD_J1)
            if en_caida:
                od = rnd.uniform(5.6, 6.6)
            fuente = "SENSOR" if est_id != 2 else "MANUAL"
            reg = "NULL" if fuente == "SENSOR" else "3"
            lecturas.append(
                f"  ({lid}, {est_id}, {temp:.2f}, {od:.2f}, {ph:.2f}, '{fuente}', {reg}, {ts(t)})"
            )
            if en_caida and alerta_abierta is None:
                alerta_abierta = {
                    "id": len(alertas) + 1,
                    "lectura": lid,
                    "valor": od,
                    "creada": t,
                }
                alertas.append(alerta_abierta)
            if not en_caida and alerta_abierta is not None:
                # La primera caída se atendió 1 h después de crearse la alerta.
                alerta_abierta["atendida"] = alerta_abierta["creada"] + timedelta(hours=1)
                alerta_abierta = None
            t += timedelta(hours=PASO_HORAS)

    out.append(
        "INSERT INTO lecturas_agua (id, estanque_id, temperatura_c, oxigeno_mg_l, ph, fuente, "
        "registrado_por, medido_en) VALUES"
    )
    out.append(",\n".join(lecturas) + ";\n")

    out.append(
        "INSERT INTO alertas (id, estanque_id, lectura_id, parametro, nivel, valor, mensaje, "
        "estado, creada_en, atendida_por, atendida_en, observacion) VALUES"
    )
    filas = []
    for a in alertas:
        msg = f"Oxígeno disuelto en precaución: {a['valor']:.2f} mg/L (normal >= 7.0)"
        if "atendida" in a:
            filas.append(
                f"  ({a['id']}, 3, {a['lectura']}, 'OXIGENO_DISUELTO', 'PRECAUCION', "
                f"{a['valor']:.2f}, '{msg}', 'ATENDIDA', {ts(a['creada'])}, 3, "
                f"{ts(a['atendida'])}, 'Se encendió el aireador')"
            )
        else:
            filas.append(
                f"  ({a['id']}, 3, {a['lectura']}, 'OXIGENO_DISUELTO', 'PRECAUCION', "
                f"{a['valor']:.2f}, '{msg}', 'ABIERTA', {ts(a['creada'])}, NULL, NULL, NULL)"
            )
    out.append(",\n".join(filas) + ";\n")

    alim = []
    aid = 0
    tasas = {1: 0.02, 2: 0.03, 3: 0.012}  # según config/alimentacion.yaml
    for lote_id, _, _, peces, _, peso_act, _ in LOTES:
        for d in range(DIAS):
            aid += 1
            kg = peces * peso_act / 1000 * tasas[lote_id] * rnd.uniform(0.95, 1.05)
            momento = INICIO + timedelta(days=d, hours=8)
            alim.append(f"  ({aid}, {lote_id}, {kg:.3f}, 3, {ts(momento)})")
    out.append(
        "INSERT INTO registros_alimentacion (id, lote_id, cantidad_kg, registrado_por, "
        "registrado_en) VALUES"
    )
    out.append(",\n".join(alim) + ";\n")

    mort = [
        f"  (1, 1, 12, 'Manipulación en biometría', 3, {ts(INICIO + timedelta(days=1, hours=17))})",
        f"  (2, 2, 25, 'Desconocida', 3, {ts(INICIO + timedelta(days=3, hours=17))})",
        f"  (3, 3, 8, 'Estrés por bajo oxígeno', 3, {ts(INICIO + timedelta(days=2, hours=17))})",
    ]
    out.append(
        "INSERT INTO registros_mortalidad (id, lote_id, cantidad, causa, registrado_por, "
        "registrado_en) VALUES"
    )
    out.append(",\n".join(mort) + ";\n")

    # Reajustar secuencias (solo PostgreSQL; tools/init_db.py omite estas líneas en SQLite).
    out.append("-- postgresql-only")
    for tabla in (
        "usuarios",
        "estanques",
        "lotes",
        "lecturas_agua",
        "alertas",
        "registros_alimentacion",
        "registros_mortalidad",
    ):
        out.append(
            f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
            f"(SELECT MAX(id) FROM {tabla}));"
        )
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    DESTINO.write_text(generar(), encoding="utf-8", newline="\n")
    print(f"Escrito {DESTINO.relative_to(RAIZ)}")
