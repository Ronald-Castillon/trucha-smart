"""Despliegue en Render (ADR-008): URL de la base y arranque idempotente de la base demo."""

import sqlite3

import pytest
import yaml

from src.adapters.config import RAIZ, normalizar_url_bd
from tools.init_db import main as init_db


@pytest.mark.parametrize(
    ("entrada", "esperada"),
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///./truchasmart.db", "sqlite:///./truchasmart.db"),
    ],
)
def test_normaliza_la_url_de_postgresql_del_proveedor(entrada, esperada):
    assert normalizar_url_bd(entrada) == esperada


def test_si_vacia_crea_la_base_una_vez_y_no_la_vuelve_a_tocar(tmp_path, capsys):
    url = f"sqlite:///{(tmp_path / 'render.db').as_posix()}"
    assert init_db(["--url", url, "--si-vacia"]) == 0
    with sqlite3.connect(tmp_path / "render.db") as cx:
        cx.execute(
            "UPDATE usuarios SET nombre_completo = 'cambiado' WHERE nombre_usuario = 'admin'"
        )
    assert init_db(["--url", url, "--si-vacia"]) == 0
    assert "ya inicializada" in capsys.readouterr().out
    with sqlite3.connect(tmp_path / "render.db") as cx:
        nombre = cx.execute("SELECT nombre_completo FROM usuarios WHERE nombre_usuario = 'admin'")
        assert nombre.fetchone()[0] == "cambiado"  # los datos existentes se conservan


def test_blueprint_de_render_declara_web_docker_y_postgresql():
    bp = yaml.safe_load((RAIZ / "render.yaml").read_text(encoding="utf-8"))
    web = bp["services"][0]
    assert web["runtime"] == "docker" and web["healthCheckPath"] == "/api/salud"
    variables = {v["key"]: v for v in web["envVars"]}
    assert variables["APP_ENV"]["value"] == "produccion"
    assert variables["JWT_SECRET"]["generateValue"] is True
    assert variables["DATABASE_URL"]["fromDatabase"]["name"] == bp["databases"][0]["name"]
