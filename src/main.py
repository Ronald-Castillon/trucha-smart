"""Raíz de composición: construye la aplicación FastAPI y conecta adaptadores con puertos."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.adapters.config import Configuracion
from src.adapters.inbound.rest import auth, estanques, salud
from src.adapters.inbound.rest.dependencias import Recursos
from src.adapters.inbound.rest.errores import registrar_manejadores
from src.adapters.inbound.web import rutas as web
from src.adapters.inbound.web.plantillas import CARPETA as CARPETA_WEB
from src.adapters.outbound.persistence.db import BaseDatos
from src.adapters.outbound.reloj_sistema import RelojSistema
from src.adapters.outbound.security.bcrypt_hasher import HasherBcrypt
from src.adapters.outbound.security.jwt_tokens import ServicioTokens

DESCRIPCION = (
    "Sistema Inteligente para Optimización de Producción Piscícola de Trucha. "
    "Las decisiones siguen siendo humanas: el sistema automatiza detección, registro y cálculo."
    "\n\nAutenticación: `POST /api/auth/login` devuelve un JWT para `Authorization: Bearer`. "
    'Errores: `{"error", "detalle", "campo"}`.'
)


def crear_recursos(config: Configuracion) -> Recursos:
    bd = BaseDatos(config.database_url)
    bd.crear_tablas()
    return Recursos(
        bd=bd,
        hasher=HasherBcrypt(),
        tokens=ServicioTokens(config.jwt_secret, config.jwt_expira_minutos),
        reloj=RelojSistema(),
    )


def crear_app(config: Configuracion | None = None, recursos: Recursos | None = None) -> FastAPI:
    """Crea la app. Los recursos (BD, etc.) se construyen al arrancar si no se inyectan."""

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
        if app.state.recursos is None:
            app.state.recursos = crear_recursos(config or Configuracion.desde_entorno())
        yield

    app = FastAPI(
        title="TruchaSmart API",
        version="1.0.0",
        description=DESCRIPCION,
        lifespan=ciclo_de_vida,
    )
    app.state.recursos = recursos
    registrar_manejadores(app)
    app.include_router(salud.router)
    app.include_router(auth.router)
    app.include_router(estanques.router)
    app.include_router(web.router)
    app.mount("/static", StaticFiles(directory=CARPETA_WEB / "static"), name="static")
    return app


app = crear_app()
