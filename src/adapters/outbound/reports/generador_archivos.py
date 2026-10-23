"""Adaptador del puerto GeneradorReportes: CSV (módulo csv) y PDF (reportlab)."""

from __future__ import annotations

import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.domain.model.lectura_agua import Parametro
from src.ports.inbound.exportar_reporte import Reporte, TipoReporte

# Un PDF muy largo no es útil para leer; el detalle completo siempre está en el CSV.
MAX_FILAS_PDF = 1500
NIVEL_CORTO = {"NORMAL": "", "PRECAUCION": " (P)", "CRITICA": " (C)"}

COLUMNAS_CALIDAD = [
    "estanque", "medido_en_utc", "temperatura_c", "nivel_temperatura", "oxigeno_mg_l",
    "nivel_oxigeno", "ph", "nivel_ph", "fuente",
]  # fmt: skip
COLUMNAS_PRODUCCION = [
    "estanque", "lote", "fecha_siembra", "estado", "peces_sembrados", "mortalidad_periodo",
    "mortalidad_total", "peces_vivos", "peso_medio_actual_g", "biomasa_kg",
    "alimento_periodo_kg", "alimento_total_kg", "fcr",
]  # fmt: skip


def _filas_calidad(reporte: Reporte):
    for f in reporte.filas_calidad:
        yield [
            f.estanque,
            f.medido_en.strftime("%Y-%m-%d %H:%M:%S"),
            f"{f.temperatura_c:.2f}",
            f.niveles[Parametro.TEMPERATURA].value,
            f"{f.oxigeno_mg_l:.2f}",
            f.niveles[Parametro.OXIGENO_DISUELTO].value,
            f"{f.ph:.2f}",
            f.niveles[Parametro.PH].value,
            f.fuente,
        ]


def _filas_produccion(reporte: Reporte):
    for f in reporte.filas_produccion:
        yield [
            f.estanque,
            f.lote,
            f.fecha_siembra.isoformat(),
            "activo" if f.activo else "cerrado",
            f.peces_sembrados,
            f.mortalidad_periodo,
            f.mortalidad_total,
            f.peces_vivos,
            f"{f.peso_medio_actual_g:.2f}",
            f"{f.biomasa_kg:.3f}",
            f"{f.alimento_periodo_kg:.3f}",
            f"{f.alimento_total_kg:.3f}",
            f.fcr,
        ]


class GeneradorReportesArchivo:
    def csv(self, reporte: Reporte) -> bytes:
        salida = io.StringIO(newline="")
        escritor = csv.writer(salida, lineterminator="\r\n")
        if reporte.tipo is TipoReporte.CALIDAD_AGUA:
            escritor.writerow(COLUMNAS_CALIDAD)
            escritor.writerows(_filas_calidad(reporte))
        else:
            escritor.writerow(COLUMNAS_PRODUCCION)
            escritor.writerows(_filas_produccion(reporte))
        # utf-8-sig: Excel abre correctamente las tildes.
        return salida.getvalue().encode("utf-8-sig")

    def pdf(self, reporte: Reporte) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            title=f"TruchaSmart - {reporte.titulo}",
            author="TruchaSmart",
        )
        estilos = getSampleStyleSheet()
        partes = [
            Paragraph(f"TruchaSmart · {reporte.titulo}", estilos["Title"]),
            Paragraph(
                f"Periodo: {reporte.desde:%d/%m/%Y} al {reporte.hasta:%d/%m/%Y} (UTC) · "
                f"Generado el {reporte.generado_en:%d/%m/%Y %H:%M} UTC por {reporte.generado_por}",
                estilos["Normal"],
            ),
            Spacer(1, 0.4 * cm),
        ]
        if reporte.tipo is TipoReporte.CALIDAD_AGUA:
            partes += self._pdf_calidad(reporte, estilos)
        else:
            partes += self._pdf_produccion(reporte, estilos)
        partes += [
            Spacer(1, 0.4 * cm),
            Paragraph(
                "Umbrales y tablas: valores de referencia parametrizables (config/*.yaml), "
                "a validar con el técnico de la piscigranja.",
                estilos["Italic"],
            ),
        ]
        doc.build(partes)
        return buffer.getvalue()

    @staticmethod
    def _tabla(datos, anchos=None) -> Table:
        tabla = Table(datos, colWidths=anchos, repeatRows=1)
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b6e8a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d5dee5")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f4f7f9")],
                    ),
                ]
            )
        )
        return tabla

    def _pdf_calidad(self, reporte: Reporte, estilos):
        def est(t):
            return "—" if t is None else f"{t[0]:.2f} / {t[1]:.2f} / {t[2]:.2f}"

        resumen = [["Estanque", "Lecturas", "T °C (mín/prom/máx)", "OD mg/L (mín/prom/máx)",
                    "pH (mín/prom/máx)", "Alertas P", "Alertas C", "Atendidas"]]  # fmt: skip
        for r in reporte.resumen_calidad:
            resumen.append(
                [
                    r.estanque,
                    r.lecturas,
                    est(r.temperatura),
                    est(r.oxigeno),
                    est(r.ph),
                    r.alertas_precaucion,
                    r.alertas_criticas,
                    r.alertas_atendidas,
                ]
            )
        partes = [Paragraph("Resumen por estanque", estilos["Heading2"]), self._tabla(resumen)]
        detalle = [["Estanque", "Fecha UTC", "T °C", "OD mg/L", "pH", "Fuente"]]
        for f in reporte.filas_calidad[:MAX_FILAS_PDF]:
            detalle.append([
                f.estanque,
                f.medido_en.strftime("%d/%m/%Y %H:%M"),
                f"{f.temperatura_c:.2f}{NIVEL_CORTO[f.niveles[Parametro.TEMPERATURA].value]}",
                f"{f.oxigeno_mg_l:.2f}{NIVEL_CORTO[f.niveles[Parametro.OXIGENO_DISUELTO].value]}",
                f"{f.ph:.2f}{NIVEL_CORTO[f.niveles[Parametro.PH].value]}",
                f.fuente.title(),
            ])  # fmt: skip
        partes += [
            Spacer(1, 0.4 * cm),
            Paragraph(
                f"Detalle de lecturas ({len(reporte.filas_calidad)}) · (P) precaución, (C) crítica",
                estilos["Heading2"],
            ),
        ]
        if len(reporte.filas_calidad) > MAX_FILAS_PDF:
            partes.append(
                Paragraph(
                    f"Se muestran las primeras {MAX_FILAS_PDF} lecturas; "
                    "el detalle completo está en el CSV.",
                    estilos["Normal"],
                )
            )
        partes.append(
            self._tabla(detalle)
            if len(detalle) > 1
            else Paragraph("Sin lecturas.", estilos["Normal"])
        )
        return partes

    def _pdf_produccion(self, reporte: Reporte, estilos):
        datos = [["Estanque", "Lote", "Siembra", "Estado", "Sembrados", "Mort. periodo",
                  "Mort. total", "Vivos", "Peso g", "Biomasa kg", "Alim. periodo kg",
                  "Alim. total kg", "FCR"]]  # fmt: skip
        for fila in _filas_produccion(reporte):
            datos.append(fila)
        if len(datos) == 1:
            return [Paragraph("Sin lotes vigentes en el periodo.", estilos["Normal"])]
        return [
            Paragraph("Producción por lote", estilos["Heading2"]),
            self._tabla(datos),
            Paragraph(
                "Biomasa = peces vivos × peso medio actual · FCR = alimento total / ganancia de "
                'biomasa ("no calculable" si la ganancia es 0).',
                estilos["Normal"],
            ),
        ]
