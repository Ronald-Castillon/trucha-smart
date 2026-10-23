"""Raíz de composición: construye la aplicación FastAPI y conecta adaptadores con puertos."""

from fastapi import FastAPI

from src.adapters.inbound.rest import salud

DESCRIPCION = (
    "Sistema Inteligente para Optimización de Producción Piscícola de Trucha. "
    "Las decisiones siguen siendo humanas: el sistema automatiza detección, registro y cálculo."
)


def crear_app() -> FastAPI:
    app = FastAPI(title="TruchaSmart API", version="0.1.0", description=DESCRIPCION)
    app.include_router(salud.router)
    return app


app = crear_app()
