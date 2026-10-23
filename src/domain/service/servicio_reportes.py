"""Caso de uso exportar_reporte: arma los datos del reporte y delega el formato (RF-08)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from src.domain.errores import ErrorValidacion
from src.domain.model.alerta import EstadoAlerta
from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Permiso, Usuario
from src.domain.service.calculadora_fcr import resumen_produccion
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.ports.inbound.exportar_reporte import (
    ArchivoReporte,
    FilaCalidad,
    FilaProduccion,
    FormatoReporte,
    Reporte,
    ResumenCalidadEstanque,
    TipoReporte,
)
from src.ports.outbound.generador_reportes import GeneradorReportes
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_alerta import RepositorioAlerta
from src.ports.outbound.repositorio_alimentacion import RepositorioAlimentacion
from src.ports.outbound.repositorio_estanque import RepositorioEstanque
from src.ports.outbound.repositorio_lectura import RepositorioLectura
from src.ports.outbound.repositorio_lote import RepositorioLote
from src.ports.outbound.repositorio_mortalidad import RepositorioMortalidad

MAXIMO_DIAS = 366
TITULOS = {
    TipoReporte.CALIDAD_AGUA: "Reporte de calidad de agua",
    TipoReporte.PRODUCCION: "Reporte de producción",
}
TIPOS_CONTENIDO = {
    FormatoReporte.CSV: "text/csv; charset=utf-8",
    FormatoReporte.PDF: "application/pdf",
}


def _estadistica(valores: list[float]) -> tuple[float, float, float] | None:
    if not valores:
        return None
    return (min(valores), round(sum(valores) / len(valores), 2), max(valores))


class ServicioReportes:
    """Implementa el puerto de entrada ExportarReporte."""

    def __init__(
        self,
        estanques: RepositorioEstanque,
        lotes: RepositorioLote,
        lecturas: RepositorioLectura,
        alertas: RepositorioAlerta,
        alimentacion: RepositorioAlimentacion,
        mortalidad: RepositorioMortalidad,
        evaluador: EvaluadorCalidadAgua,
        generador: GeneradorReportes,
        reloj: Reloj,
    ) -> None:
        self._estanques = estanques
        self._lotes = lotes
        self._lecturas = lecturas
        self._alertas = alertas
        self._alimentacion = alimentacion
        self._mortalidad = mortalidad
        self._evaluador = evaluador
        self._generador = generador
        self._reloj = reloj

    def exportar(
        self,
        tipo: TipoReporte,
        formato: FormatoReporte,
        desde: date,
        hasta: date,
        solicitante: Usuario,
    ) -> ArchivoReporte:
        solicitante.exigir(Permiso.GESTIONAR_REPORTES)
        reporte = self.armar(tipo, desde, hasta, solicitante)
        contenido = (
            self._generador.csv(reporte)
            if formato is FormatoReporte.CSV
            else self._generador.pdf(reporte)
        )
        nombre = f"truchasmart_{tipo.value}_{desde.isoformat()}_{hasta.isoformat()}.{formato.value}"
        return ArchivoReporte(nombre, TIPOS_CONTENIDO[formato], contenido)

    def armar(self, tipo: TipoReporte, desde: date, hasta: date, solicitante: Usuario) -> Reporte:
        solicitante.exigir(Permiso.GESTIONAR_REPORTES)
        if desde > hasta:
            raise ErrorValidacion("desde", "La fecha 'desde' no puede ser posterior a 'hasta'")
        if (hasta - desde).days + 1 > MAXIMO_DIAS:
            raise ErrorValidacion("desde", f"El rango máximo es de {MAXIMO_DIAS} días")
        inicio = datetime.combine(desde, time.min, tzinfo=UTC)
        fin = datetime.combine(hasta, time.max, tzinfo=UTC)
        filas_calidad, resumen_calidad, filas_produccion = [], [], []
        if tipo is TipoReporte.CALIDAD_AGUA:
            filas_calidad, resumen_calidad = self._calidad(inicio, fin)
        else:
            filas_produccion = self._produccion(desde, hasta, inicio, fin)
        return Reporte(
            tipo=tipo,
            titulo=TITULOS[tipo],
            desde=desde,
            hasta=hasta,
            generado_en=self._reloj.ahora(),
            generado_por=solicitante.nombre_completo,
            filas_calidad=filas_calidad,
            resumen_calidad=resumen_calidad,
            filas_produccion=filas_produccion,
        )

    def _calidad(self, inicio: datetime, fin: datetime):
        filas, resumen = [], []
        for e in self._estanques.listar(solo_activos=False):
            lecturas = sorted(
                self._lecturas.de_estanque(e.id, inicio, fin), key=lambda x: (x.medido_en, x.id)
            )
            for x in lecturas:
                filas.append(
                    FilaCalidad(
                        estanque=e.nombre,
                        medido_en=x.medido_en,
                        temperatura_c=x.temperatura_c,
                        oxigeno_mg_l=x.oxigeno_mg_l,
                        ph=x.ph,
                        fuente=x.fuente.value,
                        niveles=self._evaluador.niveles(x),
                    )
                )
            alertas = [a for a in self._alertas.listar(e.id) if inicio <= a.creada_en <= fin]
            if not lecturas and not alertas:
                continue
            resumen.append(
                ResumenCalidadEstanque(
                    estanque=e.nombre,
                    lecturas=len(lecturas),
                    temperatura=_estadistica([x.temperatura_c for x in lecturas]),
                    oxigeno=_estadistica([x.oxigeno_mg_l for x in lecturas]),
                    ph=_estadistica([x.valores()[Parametro.PH] for x in lecturas]),
                    alertas_precaucion=sum(a.nivel is Nivel.PRECAUCION for a in alertas),
                    alertas_criticas=sum(a.nivel is Nivel.CRITICA for a in alertas),
                    alertas_atendidas=sum(a.estado is EstadoAlerta.ATENDIDA for a in alertas),
                )
            )
        return filas, resumen

    def _produccion(self, desde: date, hasta: date, inicio: datetime, fin: datetime):
        filas = []
        for e in self._estanques.listar(solo_activos=False):
            for lote in sorted(self._lotes.de_estanque(e.id), key=lambda lo: lo.fecha_siembra):
                vigente = lote.fecha_siembra <= hasta and (
                    lote.fecha_cierre is None or lote.fecha_cierre >= desde
                )
                if not vigente:
                    continue
                mortalidad_total = self._mortalidad.total(lote.id)
                r = resumen_produccion(lote, mortalidad_total, self._alimentacion.total_kg(lote.id))
                filas.append(
                    FilaProduccion(
                        estanque=e.nombre,
                        lote=lote.codigo,
                        fecha_siembra=lote.fecha_siembra,
                        activo=lote.activo,
                        peces_sembrados=lote.num_peces_inicial,
                        mortalidad_periodo=sum(
                            m.cantidad for m in self._mortalidad.de_lote(lote.id, inicio, fin)
                        ),
                        mortalidad_total=mortalidad_total,
                        peces_vivos=r.peces_vivos,
                        peso_medio_actual_g=lote.peso_medio_actual_g,
                        biomasa_kg=r.biomasa_kg,
                        alimento_periodo_kg=round(
                            sum(
                                a.cantidad_kg
                                for a in self._alimentacion.de_lote(lote.id, inicio, fin)
                            ),
                            3,
                        ),
                        alimento_total_kg=r.alimento_total_kg,
                        fcr=r.fcr_texto,
                    )
                )
        return filas
