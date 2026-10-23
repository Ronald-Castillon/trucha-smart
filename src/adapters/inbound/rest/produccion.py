"""Router de alimentación, mortalidad y producción del lote (RF-06)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.rest.esquemas import (
    AlimentacionEntrada,
    AlimentacionSalida,
    MortalidadEntrada,
    MortalidadSalida,
    ProduccionSalida,
)
from src.domain.model.usuario import Usuario

router = APIRouter(
    prefix="/api/lotes", tags=["alimentación y producción"], responses=RESPUESTAS_ERROR
)


@router.post("/{lote_id}/alimentacion", response_model=AlimentacionSalida, status_code=201)
def registrar_alimentacion(
    lote_id: int,
    datos: AlimentacionEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> AlimentacionSalida:
    """Registra el alimento suministrado (kg > 0) a un lote activo."""
    registro = c.produccion.registrar_alimentacion(
        lote_id, datos.cantidad_kg, usuario, datos.registrado_en
    )
    c.confirmar()
    return AlimentacionSalida.de(registro)


@router.get("/{lote_id}/alimentacion", response_model=list[AlimentacionSalida])
def listar_alimentacion(
    lote_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> list[AlimentacionSalida]:
    return [AlimentacionSalida.de(r) for r in c.produccion.alimentaciones(lote_id, usuario)]


@router.post("/{lote_id}/mortalidad", response_model=MortalidadSalida, status_code=201)
def registrar_mortalidad(
    lote_id: int,
    datos: MortalidadEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> MortalidadSalida:
    """Registra peces muertos (> 0 y sin superar los peces vivos)."""
    registro = c.produccion.registrar_mortalidad(
        lote_id, datos.cantidad, datos.causa, usuario, datos.registrado_en
    )
    c.confirmar()
    return MortalidadSalida.de(registro)


@router.get("/{lote_id}/mortalidad", response_model=list[MortalidadSalida])
def listar_mortalidad(
    lote_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> list[MortalidadSalida]:
    return [MortalidadSalida.de(r) for r in c.produccion.mortalidades(lote_id, usuario)]


@router.get("/{lote_id}/produccion", response_model=ProduccionSalida)
def produccion(
    lote_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> ProduccionSalida:
    """Peces vivos, biomasa estimada (peces vivos × peso medio) y FCR
    (alimento total / ganancia de biomasa). Si la ganancia es 0, `fcr` es null y
    `fcr_texto` = "no calculable"."""
    return ProduccionSalida.de(c.produccion.produccion(lote_id, usuario))
