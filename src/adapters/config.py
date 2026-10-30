"""Configuración de la aplicación leída de variables de entorno (y de .env si existe)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import ConjuntoUmbrales, Nivel, Umbral
from src.domain.service.recomendador_racion import TablaAlimentacion, TramoTasa

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


JWT_SECRET_POR_DEFECTO = "cambia-esta-clave-por-una-larga-y-aleatoria"
LONGITUD_MINIMA_SECRETO = 32


class ConfiguracionInsegura(RuntimeError):
    """La configuración no es apta para producción (RNF-+, OWASP A02)."""


@dataclass(frozen=True)
class Configuracion:
    database_url: str = "sqlite:///./truchasmart.db"
    jwt_secret: str = JWT_SECRET_POR_DEFECTO
    jwt_expira_minutos: int = 480
    umbrales_path: Path = RAIZ / "config" / "umbrales.yaml"
    alimentacion_path: Path = RAIZ / "config" / "alimentacion.yaml"
    entorno: str = "desarrollo"  # APP_ENV: desarrollo | produccion

    @property
    def es_produccion(self) -> bool:
        return self.entorno.lower() in ("produccion", "producción", "production")

    def validar(self) -> None:
        """En producción no se arranca con la clave JWT de ejemplo ni con una clave corta."""
        if self.es_produccion and (
            self.jwt_secret == JWT_SECRET_POR_DEFECTO
            or len(self.jwt_secret) < LONGITUD_MINIMA_SECRETO
        ):
            raise ConfiguracionInsegura(
                f"APP_ENV=produccion exige JWT_SECRET propio de al menos "
                f'{LONGITUD_MINIMA_SECRETO} caracteres (p. ej. python -c "import secrets; '
                f'print(secrets.token_urlsafe(48))")'
            )

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
            entorno=e.get("APP_ENV", cls.entorno),
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


def cargar_alimentacion(ruta: Path) -> TablaAlimentacion:
    """Lee config/alimentacion.yaml (tabla de tasas y factores, ADR-005)."""
    datos = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
    niveles = {"normal": Nivel.NORMAL, "precaucion": Nivel.PRECAUCION, "critica": Nivel.CRITICA}

    def factores(clave: str) -> dict[Nivel, float]:
        return {niveles[k]: float(v) for k, v in datos[clave].items()}

    return TablaAlimentacion(
        tramos=tuple(
            TramoTasa(float(t["desde_g"]), t["hasta_g"], float(t["tasa_pct"]))
            for t in datos["tasas"]
        ),
        factor_temperatura=factores("factor_temperatura"),
        factor_oxigeno=factores("factor_oxigeno"),
    )
