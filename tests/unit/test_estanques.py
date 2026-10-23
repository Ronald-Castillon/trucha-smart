"""RF-02: estanques/jaulas y lotes (dominio)."""

from datetime import date

import pytest

from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado, PermisoDenegado
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lote import Lote
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.servicio_estanques import ServicioEstanques
from src.ports.inbound.gestionar_estanque import ComandoSembrarLote, DatosEstanque
from tests.fakes import RelojFijo, RepositorioEstanqueMemoria, RepositorioLoteMemoria

HOY = date(2026, 10, 23)


def _usuario(rol: Rol) -> Usuario:
    return Usuario("u", "U", "h", rol, RelojFijo().ahora(), id=1)


PISCICULTOR = _usuario(Rol.PISCICULTOR)
OPERARIO = _usuario(Rol.OPERARIO)


@pytest.fixture
def srv() -> ServicioEstanques:
    return ServicioEstanques(RepositorioEstanqueMemoria(), RepositorioLoteMemoria(), RelojFijo())


@pytest.fixture
def estanque(srv) -> Estanque:
    return srv.crear(DatosEstanque("Estanque A1", TipoEstanque.ESTANQUE, 120, "Norte"), PISCICULTOR)


def _sembrar(srv, estanque_id, codigo="L-1", peces=5000, peso=12.5, fecha=date(2026, 10, 1)):
    return srv.sembrar_lote(
        ComandoSembrarLote(estanque_id, codigo, peces, peso, fecha), PISCICULTOR
    )


# --------------------------------------------------------------------------- modelo


def test_estanque_valida_nombre_y_volumen():
    with pytest.raises(ErrorValidacion) as e:
        Estanque("  ", TipoEstanque.JAULA, RelojFijo().ahora())
    assert e.value.campo == "nombre"
    with pytest.raises(ErrorValidacion) as e:
        Estanque("J1", TipoEstanque.JAULA, RelojFijo().ahora(), volumen_m3=0)
    assert e.value.campo == "volumen_m3"
    assert (
        Estanque(" J1 ", TipoEstanque.JAULA, RelojFijo().ahora(), ubicacion=" ").ubicacion is None
    )


@pytest.mark.parametrize(
    ("peces", "peso", "fecha", "campo"),
    [
        (0, 10, date(2026, 10, 1), "num_peces"),
        (-5, 10, date(2026, 10, 1), "num_peces"),
        (100, 0, date(2026, 10, 1), "peso_medio_g"),
        (100, -1.5, date(2026, 10, 1), "peso_medio_g"),
        (100, 10, date(2026, 10, 24), "fecha_siembra"),
    ],
)
def test_cp_rf02_02_lote_invalido_indica_el_campo(peces, peso, fecha, campo):
    """CP-RF02-02: n.º de peces <= 0, peso medio <= 0 o fecha futura se rechazan por campo."""
    with pytest.raises(ErrorValidacion) as e:
        Lote.sembrar(1, "L-1", peces, peso, fecha, HOY)
    assert e.value.campo == campo


def test_lote_codigo_obligatorio():
    with pytest.raises(ErrorValidacion) as e:
        Lote.sembrar(1, " ", 10, 10, HOY, HOY)
    assert e.value.campo == "codigo"


def test_lote_peso_y_cierre():
    lote = Lote.sembrar(1, "L-1", 10, 10, date(2026, 10, 1), HOY)
    assert lote.peso_medio_actual_g == 10 and lote.activo
    lote.actualizar_peso(25)
    assert lote.peso_medio_actual_g == 25 and lote.peso_medio_inicial_g == 10
    with pytest.raises(ErrorValidacion):
        lote.cerrar(date(2026, 9, 30))
    lote.cerrar(HOY)
    assert not lote.activo and lote.fecha_cierre == HOY
    with pytest.raises(Conflicto):
        lote.actualizar_peso(30)


# --------------------------------------------------------------------------- servicio


def test_cp_rf02_01_crear_estanque_y_sembrar_lote(srv, estanque):
    """CP-RF02-01: el estanque aparece en el listado con su lote activo."""
    lote = _sembrar(srv, estanque.id)
    assert [e.nombre for e in srv.listar(OPERARIO)] == ["Estanque A1"]
    assert srv.lote_activo(estanque.id, OPERARIO) == lote
    assert lote.num_peces_inicial == 5000 and lote.peso_medio_actual_g == 12.5


def test_cp_rf02_02_lote_invalido_no_se_guarda(srv, estanque):
    """CP-RF02-02: un lote inválido no se guarda."""
    with pytest.raises(ErrorValidacion):
        _sembrar(srv, estanque.id, peces=0)
    assert srv.lote_activo(estanque.id, OPERARIO) is None


def test_un_solo_lote_activo_por_estanque(srv, estanque):
    lote = _sembrar(srv, estanque.id)
    with pytest.raises(Conflicto, match="ya tiene el lote activo L-1"):
        _sembrar(srv, estanque.id, codigo="L-2")
    srv.cerrar_lote(lote.id, HOY, PISCICULTOR)
    nuevo = _sembrar(srv, estanque.id, codigo="L-2")
    assert srv.lote_activo(estanque.id, OPERARIO) == nuevo
    assert len(srv.lotes_de(estanque.id, OPERARIO)) == 2


def test_codigo_de_lote_unico(srv, estanque):
    otro = srv.crear(DatosEstanque("Jaula J1", TipoEstanque.JAULA), PISCICULTOR)
    _sembrar(srv, estanque.id)
    with pytest.raises(Conflicto, match="código"):
        _sembrar(srv, otro.id)


def test_nombre_de_estanque_unico(srv, estanque):
    with pytest.raises(Conflicto):
        srv.crear(DatosEstanque("Estanque A1", TipoEstanque.JAULA), PISCICULTOR)


def test_actualizar_estanque(srv, estanque):
    srv.crear(DatosEstanque("Jaula J1", TipoEstanque.JAULA), PISCICULTOR)
    act = srv.actualizar(
        estanque.id, DatosEstanque("A1 renovado", TipoEstanque.JAULA, 200), PISCICULTOR
    )
    assert (
        act.nombre == "A1 renovado"
        and act.volumen_m3 == 200
        and act.creado_en == estanque.creado_en
    )
    same = srv.actualizar(
        estanque.id, DatosEstanque("A1 renovado", TipoEstanque.JAULA), PISCICULTOR
    )
    assert same.volumen_m3 is None
    with pytest.raises(Conflicto):
        srv.actualizar(estanque.id, DatosEstanque("Jaula J1", TipoEstanque.JAULA), PISCICULTOR)


def test_desactivar_estanque(srv, estanque):
    lote = _sembrar(srv, estanque.id)
    with pytest.raises(Conflicto):
        srv.desactivar(estanque.id, PISCICULTOR)
    srv.cerrar_lote(lote.id, HOY, PISCICULTOR)
    srv.desactivar(estanque.id, PISCICULTOR)
    assert srv.listar(OPERARIO) == []
    with pytest.raises(Conflicto, match="dado de baja"):
        _sembrar(srv, estanque.id, codigo="L-9")


def test_actualizar_peso_por_servicio(srv, estanque):
    lote = _sembrar(srv, estanque.id)
    assert srv.actualizar_peso(lote.id, 30, PISCICULTOR).peso_medio_actual_g == 30
    assert srv.obtener_lote(lote.id, OPERARIO).peso_medio_actual_g == 30


def test_operario_consulta_pero_no_gestiona(srv, estanque):
    assert srv.obtener(estanque.id, OPERARIO) == estanque
    with pytest.raises(PermisoDenegado):
        srv.crear(DatosEstanque("X", TipoEstanque.JAULA), OPERARIO)
    with pytest.raises(PermisoDenegado):
        _sembrar_como(srv, estanque.id, OPERARIO)


def _sembrar_como(srv, estanque_id, usuario):
    return srv.sembrar_lote(ComandoSembrarLote(estanque_id, "L", 1, 1, HOY), usuario)


def test_no_encontrado(srv):
    with pytest.raises(NoEncontrado):
        srv.obtener(99, OPERARIO)
    with pytest.raises(NoEncontrado):
        srv.obtener_lote(99, OPERARIO)
    with pytest.raises(NoEncontrado):
        _sembrar(srv, 99)
