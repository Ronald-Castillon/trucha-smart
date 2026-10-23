"""Router de historial, tendencias e índice de riesgo (RF-05)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.rest.esquemas import HistorialSalida, RiesgoSalida
from src.domain.model.usuario import Usuario

router = APIRouter(prefix="/api", tags=["historial y riesgo"], responses=RESPUESTAS_ERROR)


@router.get("/estanques/{estanque_id}/historial", response_model=HistorialSalida)
def historial(
    estanque_id: int,
    desde: date | None = None,
    hasta: date | None = None,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> HistorialSalida:
    """Lecturas del estanque entre `desde` y `hasta` (fechas UTC, inclusivas; por defecto los
    últimos 7 días), con el nivel de cada parámetro y min/máx/promedio por parámetro."""
    return HistorialSalida.de(c.historial.historial(estanque_id, usuario, desde, hasta))


@router.get("/estanques/{estanque_id}/riesgo", response_model=RiesgoSalida)
def riesgo(
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> RiesgoSalida:
    """Índice de riesgo 0–100 con semáforo (verde < 30, amarillo 30–59, rojo >= 60)."""
    return RiesgoSalida.de(c.historial.riesgo(estanque_id, usuario))
