"""RF-09: claves de integración y API externa de solo lectura (dominio)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from src.domain.errores import ClaveInvalida, ErrorValidacion, NoEncontrado, PermisoDenegado
from src.domain.model.clave_integracion import ClaveIntegracion, huella
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua, Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.servicio_integraciones import ServicioIntegraciones
from tests.fakes import (
    RelojFijo,
    RepositorioAlertaMemoria,
    RepositorioClaveIntegracionMemoria,
    RepositorioEstanqueMemoria,
    RepositorioLecturaMemoria,
)
from tests.umbrales import UMBRALES

ADMIN = Usuario("admin", "Ana", "h", Rol.ADMINISTRADOR, RelojFijo().ahora(), id=1)
PISCICULTOR = Usuario("p", "Pedro", "h", Rol.PISCICULTOR, RelojFijo().ahora(), id=2)


@pytest.fixture
def entorno():
    reloj = RelojFijo(datetime(2026, 10, 23, 12, tzinfo=UTC))
    estanques = RepositorioEstanqueMemoria()
    eid = estanques.guardar(Estanque("A1", TipoEstanque.ESTANQUE, reloj.ahora())).id
    lecturas = RepositorioLecturaMemoria()
    for dia, od in ((20, 8.0), (21, 6.0), (22, 4.5)):
        lecturas.guardar(
            LecturaAgua(
                eid, 12.0, od, 7.2, FuenteLectura.SENSOR, datetime(2026, 10, dia, 8, tzinfo=UTC)
            )
        )
    srv = ServicioIntegraciones(
        RepositorioClaveIntegracionMemoria(),
        estanques,
        lecturas,
        RepositorioAlertaMemoria(),
        EvaluadorCalidadAgua(UMBRALES),
        reloj,
    )
    return srv, reloj, eid


def test_clave_nueva_guarda_solo_la_huella():
    entidad, secreto = ClaveIntegracion.nueva("ERP", 1, RelojFijo().ahora())
    assert secreto.startswith("ts_") and len(secreto) > 40
    assert entidad.hash_clave == huella(secreto) and secreto not in entidad.hash_clave
    assert entidad.prefijo == secreto[:11] and entidad.corresponde(secreto)
    assert not entidad.corresponde(secreto + "x")
    entidad.revocar()
    assert not entidad.corresponde(secreto)


def test_nombre_de_integracion_valido():
    with pytest.raises(ErrorValidacion):
        ClaveIntegracion.nueva("ab", 1, RelojFijo().ahora())


def test_cp_rf09_01_clave_valida_consulta_estado_y_lecturas(entorno):
    """CP-RF09-01: con una clave activa se obtienen el estado y las lecturas por rango."""
    srv, reloj, eid = entorno
    creada = srv.crear("ERP de la piscigranja", ADMIN)
    reloj.avanzar(minutes=5)
    clave = srv.autenticar(creada.secreto)
    assert clave.ultimo_uso == reloj.ahora()
    (estado,) = srv.estado_estanques(clave)
    assert estado.estanque.nombre == "A1" and estado.ultima_lectura.oxigeno_mg_l == 4.5
    assert estado.niveles[Parametro.OXIGENO_DISUELTO] is Nivel.CRITICA
    datos = srv.lecturas(clave, eid, date(2026, 10, 21), date(2026, 10, 22))
    assert [x.oxigeno_mg_l for x in datos] == [6.0, 4.5]
    assert len(srv.lecturas(clave, eid, None, None)) == 3  # últimos 7 días


@pytest.mark.parametrize("secreto", [None, "", "ts_inexistente"])
def test_cp_rf09_02_clave_inexistente(entorno, secreto):
    """CP-RF09-02: sin clave o con una clave desconocida -> ClaveInvalida (401)."""
    srv, *_ = entorno
    with pytest.raises(ClaveInvalida):
        srv.autenticar(secreto)


def test_cp_rf09_02_clave_revocada(entorno):
    """CP-RF09-02: una clave revocada deja de funcionar."""
    srv, *_ = entorno
    creada = srv.crear("ERP", ADMIN)
    clave = srv.autenticar(creada.secreto)
    srv.revocar(creada.clave.id, ADMIN)
    with pytest.raises(ClaveInvalida):
        srv.autenticar(creada.secreto)
    clave.activa = False
    with pytest.raises(ClaveInvalida):
        srv.estado_estanques(clave)


def test_solo_admin_gestiona_claves_y_validaciones(entorno):
    srv, reloj, eid = entorno
    with pytest.raises(PermisoDenegado):
        srv.crear("ERP", PISCICULTOR)
    creada = srv.crear("ERP", ADMIN)
    assert [c.nombre for c in srv.listar(ADMIN)] == ["ERP"]
    with pytest.raises(NoEncontrado):
        srv.revocar(99, ADMIN)
    clave = srv.autenticar(creada.secreto)
    with pytest.raises(NoEncontrado):
        srv.lecturas(clave, 99, None, None)
    with pytest.raises(ErrorValidacion, match="posterior"):
        srv.lecturas(clave, eid, date(2026, 10, 22), date(2026, 10, 20))
    with pytest.raises(ErrorValidacion, match="31"):
        srv.lecturas(clave, eid, date(2026, 8, 1), date(2026, 10, 22))
    assert srv.lecturas(clave, eid, reloj.ahora().date() - timedelta(days=1), None)
