"""Motor de plantillas Jinja2 compartido por las vistas web."""

from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from src.domain.model.usuario import Permiso

CARPETA = Path(__file__).parent
plantillas = Jinja2Templates(directory=CARPETA / "templates")
plantillas.env.globals["P"] = Permiso


def render(request: Request, nombre: str, estado: int = 200, **contexto):
    return plantillas.TemplateResponse(request, nombre, contexto, status_code=estado)
