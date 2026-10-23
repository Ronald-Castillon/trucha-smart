"""Pruebas de la herramienta de pureza del dominio (M1.1)."""

from pathlib import Path

import pytest

from tools.check_domain_purity import analizar_paquete, main


def _crear(raiz: Path, rel: str, contenido: str = "") -> None:
    ruta = raiz / rel
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    for paq in ("src", "src/domain", "src/domain/model", "src/ports", "src/adapters"):
        _crear(tmp_path, f"{paq}/__init__.py")
    _crear(tmp_path, "src/domain/model/limpio.py", "from dataclasses import dataclass\n")
    _crear(tmp_path, "src/ports/puerto.py", "from src.domain.model.limpio import dataclass\n")
    return tmp_path


def test_dominio_limpio_da_cero_y_exit_0(proyecto: Path, capsys):
    assert main(["--raiz", str(proyecto)]) == 0
    assert "M1.1 = 0 /" in capsys.readouterr().out


def test_import_de_framework_contamina_y_exit_1(proyecto: Path, capsys):
    _crear(proyecto, "src/domain/model/sucio.py", "import sqlalchemy\nfrom pydantic import X\n")
    resultado = analizar_paquete(proyecto, "src.domain")
    assert [m.ruta.name for m in resultado.contaminados] == ["sucio.py"]
    assert main(["--raiz", str(proyecto)]) == 1
    assert "M1.1 = 1 / 4 x 100 = 25.0 %" in capsys.readouterr().out


def test_import_relativo_hacia_adapters_se_detecta(proyecto: Path):
    _crear(proyecto, "src/domain/model/rel.py", "from ...adapters import algo\n")
    sucios = analizar_paquete(proyecto, "src.domain").contaminados
    assert sucios and "src.adapters" in sucios[0].imports_prohibidos[0]


def test_import_relativo_dentro_del_dominio_es_valido(proyecto: Path):
    _crear(proyecto, "src/domain/model/rel.py", "from .limpio import dataclass\n")
    assert analizar_paquete(proyecto, "src.domain").contaminados == []


def test_puerto_contaminado_tambien_falla(proyecto: Path):
    _crear(proyecto, "src/ports/malo.py", "from fastapi import APIRouter\n")
    assert main(["--raiz", str(proyecto)]) == 1


def test_repositorio_real_es_puro():
    raiz = Path(__file__).resolve().parents[2]
    assert analizar_paquete(raiz, "src.domain").contaminados == []
    assert analizar_paquete(raiz, "src.ports").contaminados == []
