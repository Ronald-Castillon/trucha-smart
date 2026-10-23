"""Endpoint de salud del servicio (usado por docker-compose y monitoreo)."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["salud"])


class EstadoSalud(BaseModel):
    estado: str
    servicio: str


@router.get("/salud", response_model=EstadoSalud, summary="Estado del servicio")
def salud() -> EstadoSalud:
    return EstadoSalud(estado="ok", servicio="TruchaSmart")
