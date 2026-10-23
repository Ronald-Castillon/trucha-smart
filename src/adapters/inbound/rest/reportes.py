"""Router de exportación de reportes PDF y CSV (RF-08)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Response

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.domain.model.usuario import Usuario
from src.ports.inbound.exportar_reporte import ArchivoReporte, FormatoReporte, TipoReporte

router = APIRouter(prefix="/api", tags=["reportes"], responses=RESPUESTAS_ERROR)


def respuesta_archivo(archivo: ArchivoReporte) -> Response:
    return Response(
        content=archivo.contenido,
        media_type=archivo.tipo_contenido,
        headers={"Content-Disposition": f'attachment; filename="{archivo.nombre}"'},
    )


@router.get(
    "/reportes/{tipo}.{formato}",
    response_class=Response,
    responses={
        200: {
            "content": {"text/csv": {}, "application/pdf": {}},
            "description": "Archivo del reporte (descarga)",
        }
    },
)
def exportar_reporte(
    tipo: TipoReporte,
    formato: FormatoReporte,
    desde: date,
    hasta: date,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> Response:
    """Reporte de `calidad-agua` o `produccion` en `csv` o `pdf` para el rango de fechas UTC
    (inclusivo). Requiere rol Piscicultor o Administrador. Rango inválido → 422."""
    return respuesta_archivo(c.reportes.exportar(tipo, formato, desde, hasta, usuario))
