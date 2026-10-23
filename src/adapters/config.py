"""Configuración de la aplicación leída de variables de entorno (y de .env si existe)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import ConjuntoUmbrales, Umbral

RAIZ = Path(__file__).resolve().parents[2]


def cargar_dotenv(ruta: Path = RAIZ / ".env") -> None:
    """Carga KEY=VALUE de .env sin sobrescribir variables ya definidas."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def _ruta(valor: str) -> Path:
    p = Path(valor)
    return p if p.is_absolute() else RAIZ / p


@dataclass(frozen=True)
class Configuracion:
    database_url: str = "sqlite:///./truchasmart.db"
    jwt_secret: str = "cambia-esta-clave-por-una-larga-y-aleatoria"
    jwt_expira_minutos: int = 480
    umbrales_path: Path = RAIZ / "config" / "umbrales.yaml"
    alimentacion_path: Path = RAIZ / "config" / "alimentacion.yaml"

    @classmethod
    def desde_entorno(cls) -> Configuracion:
        cargar_dotenv()
        e = os.environ
        return cls(
            database_url=e.get("DATABASE_URL", cls.database_url),
            jwt_secret=e.get("JWT_SECRET", cls.jwt_secret),
            jwt_expira_minutos=int(e.get("JWT_EXPIRA_MINUTOS", cls.jwt_expira_minutos)),
            umbrales_path=_ruta(e.get("UMBRALES_PATH", "config/umbrales.yaml")),
            alimentacion_path=_ruta(e.get("ALIMENTACION_PATH", "config/alimentacion.yaml")),
        )


def cargar_umbrales(ruta: Path) -> ConjuntoUmbrales:
    """Lee config/umbrales.yaml y construye los umbrales del dominio (ADR-005)."""
    datos = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))

    def umbral(clave: str, parametro: Parametro) -> Umbral:
        d = datos[clave]
        normal = d["normal"]
        precaucion = d["precaucion"]
        return Umbral(
            parametro=parametro,
            unidad=d.get("unidad", ""),
            normal_min=normal[0],
            normal_max=normal[1],
            precaucion_min=precaucion[0],
            precaucion_max=precaucion[1],
        )

    return ConjuntoUmbrales(
        temperatura=umbral("temperatura", Parametro.TEMPERATURA),
        oxigeno_disuelto=umbral("oxigeno_disuelto", Parametro.OXIGENO_DISUELTO),
        ph=umbral("ph", Parametro.PH),
    )
