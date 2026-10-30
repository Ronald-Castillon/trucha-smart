"""Endpoint de salud del servicio (docker-compose, monitoreo y pruebas de confiabilidad, RNF-R)."""

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["salud"])


class EstadoSalud(BaseModel):
    estado: str
    servicio: str
    base_datos: str


@router.get(
    "/salud",
    response_model=EstadoSalud,
    summary="Estado del servicio y de la base de datos",
    responses={503: {"model": EstadoSalud, "description": "La base de datos no responde"}},
)
def salud(request: Request, response: Response) -> EstadoSalud:
    """200 si la API y la base de datos responden; 503 (sin caerse) si la base de datos no."""
    if request.app.state.recursos.bd.disponible():
        return EstadoSalud(estado="ok", servicio="TruchaSmart", base_datos="ok")
    response.status_code = 503
    return EstadoSalud(estado="degradado", servicio="TruchaSmart", base_datos="no disponible")
