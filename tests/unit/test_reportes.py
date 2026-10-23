"""RF-08: armado de reportes de calidad de agua y producción (dominio)."""

from datetime import UTC, date, datetime

import pytest

from src.domain.errores import ErrorValidacion, PermisoDenegado
from src.domain.model.alerta import Alerta, EstadoAlerta
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua, Parametro
from src.domain.model.lote import Lote
from src.domain.model.registro_alimentacion import RegistroAlimentacion
from src.domain.model.registro_mortalidad import RegistroMortalidad
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.servicio_reportes import ServicioReportes
from src.ports.inbound.exportar_reporte import FormatoReporte, TipoReporte
from tests.fakes import (
    RelojFijo,
    RepositorioAlertaMemoria,
    RepositorioAlimentacionMemoria,
    RepositorioEstanqueMemoria,
    RepositorioLecturaMemoria,
    RepositorioLoteMemoria,
    RepositorioMortalidadMemoria,
)
from tests.umbrales import UMBRALES

PISCICULTOR = Usuario("p", "Pedro P", "h", Rol.PISCICULTOR, RelojFijo().ahora(), id=2)
OPERARIO = Usuario("o", "Olga", "h", Rol.OPERARIO, RelojFijo().ahora(), id=3)


def dt(d, h=8):
    return datetime(2026, 10, d, h, tzinfo=UTC)


class GeneradorFalso:
    def __init__(self):
        self.ultimo = None

    def csv(self, reporte):
        self.ultimo = reporte
        return b"csv"

    def pdf(self, reporte):
        self.ultimo = reporte
        return b"%PDF"


@pytest.fixture
def entorno():
    estanques = RepositorioEstanqueMemoria()
    a = estanques.guardar(Estanque("A1", TipoEstanque.ESTANQUE, dt(1))).id
    b = estanques.guardar(Estanque("B1", TipoEstanque.JAULA, dt(1))).id
    estanques.guardar(Estanque("Vacío", TipoEstanque.JAULA, dt(1)))
    lotes = RepositorioLoteMemoria()
    lotes.guardar(Lote(a, "L-A", 1000, 50, 80, date(2026, 9, 1)))
    lotes.guardar(Lote(b, "L-B-viejo", 10, 1, 1, date(2026, 1, 1), activo=False,
                       fecha_cierre=date(2026, 3, 1)))  # fmt: skip
    lecturas = RepositorioLecturaMemoria()
    for d, od in ((15, 8.0), (16, 6.0), (17, 4.5), (20, 8.0)):
        lecturas.guardar(LecturaAgua(a, 12.0, od, 7.2, FuenteLectura.SENSOR, dt(d)))
    alertas = RepositorioAlertaMemoria()
    alertas.guardar(Alerta(a, 2, Parametro.OXIGENO_DISUELTO, Nivel.PRECAUCION, 6, "x", dt(16)))
    alertas.guardar(
        Alerta(a, 3, Parametro.OXIGENO_DISUELTO, Nivel.CRITICA, 4.5, "x", dt(17),
               estado=EstadoAlerta.ATENDIDA, atendida_por=3, atendida_en=dt(17, 9))
    )  # fmt: skip
    alertas.guardar(Alerta(b, 9, Parametro.PH, Nivel.CRITICA, 9.5, "x", dt(16)))  # sin lecturas
    alimentacion = RepositorioAlimentacionMemoria()
    alimentacion.guardar(RegistroAlimentacion(1, 10.0, dt(10)))
    alimentacion.guardar(RegistroAlimentacion(1, 25.04, dt(16)))
    mortalidad = RepositorioMortalidadMemoria()
    mortalidad.guardar(RegistroMortalidad(1, 4, dt(10)))
    mortalidad.guardar(RegistroMortalidad(1, 6, dt(16)))
    generador = GeneradorFalso()
    srv = ServicioReportes(
        estanques, lotes, lecturas, alertas, alimentacion, mortalidad,
        EvaluadorCalidadAgua(UMBRALES), generador, RelojFijo(),
    )  # fmt: skip
    return srv, generador


def test_cp_rf08_01_reporte_calidad_filtra_el_rango(entorno):
    """CP-RF08-01: el reporte de calidad incluye solo lecturas y alertas del rango."""
    srv, gen = entorno
    archivo = srv.exportar(
        TipoReporte.CALIDAD_AGUA, FormatoReporte.CSV, date(2026, 10, 15), date(2026, 10, 17),
        PISCICULTOR,
    )  # fmt: skip
    assert archivo.contenido == b"csv" and archivo.tipo_contenido.startswith("text/csv")
    assert archivo.nombre == "truchasmart_calidad-agua_2026-10-15_2026-10-17.csv"
    r = gen.ultimo
    assert [f.oxigeno_mg_l for f in r.filas_calidad] == [8.0, 6.0, 4.5]
    assert r.filas_calidad[2].niveles[Parametro.OXIGENO_DISUELTO] is Nivel.CRITICA
    res, res_b = r.resumen_calidad  # "Vacío" no tiene datos en el rango
    assert (res_b.estanque, res_b.lecturas, res_b.ph, res_b.alertas_criticas) == ("B1", 0, None, 1)
    assert (res.estanque, res.lecturas) == ("A1", 3)
    assert res.oxigeno == (4.5, 6.17, 8.0)
    assert (res.alertas_precaucion, res.alertas_criticas, res.alertas_atendidas) == (1, 1, 1)
    assert r.generado_por == "Pedro P" and r.filas_produccion == []


def test_cp_rf08_01_reporte_produccion(entorno):
    """CP-RF08-01: producción por lote vigente con alimento y mortalidad del periodo."""
    srv, gen = entorno
    srv.exportar(
        TipoReporte.PRODUCCION, FormatoReporte.PDF, date(2026, 10, 15), date(2026, 10, 31),
        PISCICULTOR,
    )  # fmt: skip
    (fila,) = gen.ultimo.filas_produccion  # el lote cerrado en marzo no está vigente
    assert (fila.lote, fila.mortalidad_periodo, fila.mortalidad_total) == ("L-A", 6, 10)
    assert (fila.alimento_periodo_kg, fila.alimento_total_kg) == (25.04, 35.04)
    assert (fila.peces_vivos, fila.biomasa_kg, fila.fcr) == (990, 79.2, "1.20")


def test_cp_rf08_02_rango_invalido(entorno):
    """CP-RF08-02: fecha de inicio posterior a la de fin -> error de validación (422)."""
    srv, _ = entorno
    with pytest.raises(ErrorValidacion, match="posterior"):
        srv.exportar(TipoReporte.PRODUCCION, FormatoReporte.PDF, date(2026, 10, 20),
                     date(2026, 10, 1), PISCICULTOR)  # fmt: skip
    with pytest.raises(ErrorValidacion, match="366"):
        srv.armar(TipoReporte.PRODUCCION, date(2025, 1, 1), date(2026, 10, 1), PISCICULTOR)


def test_solo_piscicultor_o_admin_exportan(entorno):
    srv, _ = entorno
    with pytest.raises(PermisoDenegado):
        srv.exportar(TipoReporte.PRODUCCION, FormatoReporte.CSV, date(2026, 10, 1),
                     date(2026, 10, 2), OPERARIO)  # fmt: skip
