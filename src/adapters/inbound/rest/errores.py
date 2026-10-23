"""Traducción consistente de errores a respuestas HTTP.

Formato JSON de error en toda la API:
    {"error": "<codigo>", "detalle": "<mensaje legible>", "campo": "<campo o null>"}
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from src.adapters.inbound.rest.dependencias import NoAutenticado
from src.domain.errores import (
    Conflicto,
    CredencialesInvalidas,
    ErrorDominio,
    ErrorValidacion,
    NoEncontrado,
    PermisoDenegado,
)


class RespuestaError(BaseModel):
    error: str
    detalle: str
    campo: str | None = None


RESPUESTAS_ERROR = {
    401: {"model": RespuestaError, "description": "No autenticado o credenciales inválidas"},
    403: {"model": RespuestaError, "description": "El rol no tiene permiso"},
    404: {"model": RespuestaError, "description": "Recurso no encontrado"},
    409: {"model": RespuestaError, "description": "Conflicto con el estado actual"},
    422: {"model": RespuestaError, "description": "Datos inválidos"},
}

_MAPA: list[tuple[type[ErrorDominio], int, str]] = [
    (ErrorValidacion, 422, "validacion"),
    (CredencialesInvalidas, 401, "credenciales_invalidas"),
    (PermisoDenegado, 403, "permiso_denegado"),
    (NoEncontrado, 404, "no_encontrado"),
    (Conflicto, 409, "conflicto"),
]


def _json(estado: int, error: str, detalle: str, campo: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=estado, content={"error": error, "detalle": detalle, "campo": campo}
    )


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDominio)
    async def _dominio(request: Request, exc: ErrorDominio):
        estado, codigo = next(
            ((e, c) for tipo, e, c in _MAPA if isinstance(exc, tipo)), (400, "error_dominio")
        )
        if not request.url.path.startswith("/api"):
            from src.adapters.inbound.web.plantillas import render

            return render(
                request,
                "error.html",
                estado,
                titulo_error="No se pudo completar la acción",
                mensaje=exc.mensaje,
            )
        return _json(estado, codigo, exc.mensaje, getattr(exc, "campo", None))

    @app.exception_handler(NoAutenticado)
    async def _no_autenticado(request: Request, exc: NoAutenticado):
        if request.url.path.startswith("/api"):
            return _json(401, "no_autenticado", "Debe iniciar sesión")
        return RedirectResponse("/login", status_code=303)

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError):
        errores = exc.errors()
        primero = errores[0] if errores else {}
        loc = [str(p) for p in primero.get("loc", ()) if p not in ("body", "query", "path")]
        campo = ".".join(loc) or None
        detalle = f"{campo}: {primero.get('msg', 'dato inválido')}" if campo else "Datos inválidos"
        return _json(422, "validacion", detalle, campo)
