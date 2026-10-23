"""Router de estanques/jaulas y lotes (RF-02)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.rest.esquemas import (
    CierreEntrada,
    EstanqueEntrada,
    EstanqueSalida,
    LoteEntrada,
    LoteSalida,
    PesoEntrada,
)
from src.domain.model.usuario import Usuario
from src.ports.inbound.gestionar_estanque import ComandoSembrarLote, DatosEstanque

router = APIRouter(prefix="/api", tags=["estanques y lotes"], responses=RESPUESTAS_ERROR)


def _datos(e: EstanqueEntrada) -> DatosEstanque:
    return DatosEstanque(e.nombre, e.tipo, e.volumen_m3, e.ubicacion)


@router.get("/estanques", response_model=list[EstanqueSalida])
def listar_estanques(
    usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> list[EstanqueSalida]:
    """Estanques activos con su lote activo (si lo tienen)."""
    return [
        EstanqueSalida.de(e, c.estanques.lote_activo(e.id, usuario))
        for e in c.estanques.listar(usuario)
    ]


@router.post("/estanques", response_model=EstanqueSalida, status_code=201)
def crear_estanque(
    datos: EstanqueEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> EstanqueSalida:
    estanque = c.estanques.crear(_datos(datos), usuario)
    c.confirmar()
    return EstanqueSalida.de(estanque)


@router.get("/estanques/{estanque_id}", response_model=EstanqueSalida)
def obtener_estanque(
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> EstanqueSalida:
    estanque = c.estanques.obtener(estanque_id, usuario)
    return EstanqueSalida.de(estanque, c.estanques.lote_activo(estanque_id, usuario))


@router.put("/estanques/{estanque_id}", response_model=EstanqueSalida)
def actualizar_estanque(
    estanque_id: int,
    datos: EstanqueEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> EstanqueSalida:
    estanque = c.estanques.actualizar(estanque_id, _datos(datos), usuario)
    c.confirmar()
    return EstanqueSalida.de(estanque, c.estanques.lote_activo(estanque_id, usuario))


@router.delete("/estanques/{estanque_id}", status_code=204)
def desactivar_estanque(
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> Response:
    """Baja lógica: se conserva el historial. Falla con 409 si tiene un lote activo."""
    c.estanques.desactivar(estanque_id, usuario)
    c.confirmar()
    return Response(status_code=204)


@router.get("/estanques/{estanque_id}/lotes", response_model=list[LoteSalida])
def lotes_de_estanque(
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> list[LoteSalida]:
    return [LoteSalida.de(lo) for lo in c.estanques.lotes_de(estanque_id, usuario)]


@router.post("/estanques/{estanque_id}/lotes", response_model=LoteSalida, status_code=201)
def sembrar_lote(
    estanque_id: int,
    datos: LoteEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> LoteSalida:
    """Siembra un lote (n.º de peces > 0, peso medio > 0). Un único lote activo por estanque."""
    lote = c.estanques.sembrar_lote(
        ComandoSembrarLote(
            estanque_id, datos.codigo, datos.num_peces, datos.peso_medio_g, datos.fecha_siembra
        ),
        usuario,
    )
    c.confirmar()
    return LoteSalida.de(lote)


@router.get("/lotes/{lote_id}", response_model=LoteSalida)
def obtener_lote(
    lote_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> LoteSalida:
    return LoteSalida.de(c.estanques.obtener_lote(lote_id, usuario))


@router.put("/lotes/{lote_id}/peso", response_model=LoteSalida)
def actualizar_peso_lote(
    lote_id: int,
    datos: PesoEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> LoteSalida:
    """Registra el peso medio de la última biometría."""
    lote = c.estanques.actualizar_peso(lote_id, datos.peso_medio_g, usuario)
    c.confirmar()
    return LoteSalida.de(lote)


@router.post("/lotes/{lote_id}/cerrar", response_model=LoteSalida)
def cerrar_lote(
    lote_id: int,
    datos: CierreEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> LoteSalida:
    lote = c.estanques.cerrar_lote(lote_id, datos.fecha_cierre, usuario)
    c.confirmar()
    return LoteSalida.de(lote)
