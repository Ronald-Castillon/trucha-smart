"""Crea el esquema (db/schema.sql) y carga los datos demo (db/seed.sql) en DATABASE_URL.

- PostgreSQL: ejecuta los scripts tal cual (docker-compose ya lo hace al crear el volumen).
- SQLite: aplica una traducción mínima de dialecto (ADR-003):
    SERIAL PRIMARY KEY -> INTEGER PRIMARY KEY AUTOINCREMENT, TIMESTAMPTZ -> TIMESTAMP,
    se quita el sufijo "+00" de las fechas y se omite el bloque "-- postgresql-only".

Uso:  python tools/init_db.py [--url sqlite:///./truchasmart.db] [--sin-seed] [--recrear]
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCHEMA = RAIZ / "db" / "schema.sql"
SEED = RAIZ / "db" / "seed.sql"
_MARCA_TIEMPO = re.compile(r"'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\+00'")


def a_sqlite(sql: str) -> str:
    sql = sql.split("-- postgresql-only")[0]
    sql = sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    sql = sql.replace("TIMESTAMPTZ", "TIMESTAMP")
    # SQLAlchemy guarda las fechas en SQLite como 'AAAA-MM-DD HH:MM:SS.ffffff' y compara como
    # texto: sin los microsegundos, '... 00:00:00' quedaría fuera de un rango que empieza en
    # '... 00:00:00.000000' (Issue #19).
    return _MARCA_TIEMPO.sub(lambda m: f"'{m.group(1)}.000000'", sql)


def cargar_sqlite(conexion: sqlite3.Connection, con_seed: bool = True) -> None:
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.executescript(a_sqlite(SCHEMA.read_text(encoding="utf-8")))
    if con_seed:
        conexion.executescript(a_sqlite(SEED.read_text(encoding="utf-8")))
    conexion.commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inicializa la base de datos")
    parser.add_argument("--url", default=os.getenv("DATABASE_URL", "sqlite:///./truchasmart.db"))
    parser.add_argument("--sin-seed", action="store_true")
    parser.add_argument("--recrear", action="store_true", help="SQLite: borra el archivo antes")
    args = parser.parse_args(argv)

    if args.url.startswith("sqlite:///"):
        ruta = Path(args.url.removeprefix("sqlite:///"))
        if args.recrear and ruta.exists():
            ruta.unlink()
        with sqlite3.connect(ruta) as cx:
            cargar_sqlite(cx, con_seed=not args.sin_seed)
        print(f"SQLite inicializada en {ruta}")
        return 0

    from sqlalchemy import create_engine

    motor = create_engine(args.url)
    with motor.begin() as cx:
        cx.exec_driver_sql(SCHEMA.read_text(encoding="utf-8"))
        if not args.sin_seed:
            cx.exec_driver_sql(SEED.read_text(encoding="utf-8"))
    print("Base de datos inicializada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
