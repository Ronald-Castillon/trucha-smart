"""RF-11: bloqueo por intentos fallidos y bitácora de seguridad (dominio)."""

import pytest

from src.domain.errores import CredencialesInvalidas, CuentaBloqueada, PermisoDenegado
from src.domain.model.evento_seguridad import TipoEvento
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.servicio_auditoria import ServicioAuditoria
from src.domain.service.servicio_usuarios import ServicioUsuarios
from tests.fakes import (
    HasherFalso,
    RelojFijo,
    RepositorioEventoSeguridadMemoria,
    RepositorioUsuarioMemoria,
)

IP = "203.0.113.7"


@pytest.fixture
def entorno():
    reloj = RelojFijo()
    usuarios = RepositorioUsuarioMemoria()
    usuarios.guardar(Usuario("operario", "Olga", "hash:Oper123!", Rol.OPERARIO, reloj.ahora()))
    admin = usuarios.guardar(
        Usuario("admin", "Ana", "hash:Admin123!", Rol.ADMINISTRADOR, reloj.ahora())
    )
    auditoria = ServicioAuditoria(RepositorioEventoSeguridadMemoria(), reloj)
    return ServicioUsuarios(usuarios, HasherFalso(), reloj, auditoria), auditoria, reloj, admin


def test_cp_rf11_01_tres_fallos_bloquean_cinco_minutos(entorno):
    """CP-RF11-01: tras 3 fallos seguidos ni la contraseña correcta entra hasta pasados 5 min."""
    srv, _, reloj, _ = entorno
    for _ in range(2):
        with pytest.raises(CredencialesInvalidas):
            srv.autenticar("operario", "mala", IP)
    with pytest.raises(CuentaBloqueada) as bloqueo:
        srv.autenticar("operario", "mala", IP)
    assert "Intente de nuevo en 5 min" in bloqueo.value.mensaje
    reloj.avanzar(minutes=4, seconds=59)
    with pytest.raises(CuentaBloqueada, match="1 min"):
        srv.autenticar("operario", "Oper123!", IP)
    reloj.avanzar(seconds=1)
    assert srv.autenticar("operario", "Oper123!", IP).nombre_usuario == "operario"


def test_un_acierto_reinicia_el_contador(entorno):
    srv, *_ = entorno
    for _ in range(2):
        with pytest.raises(CredencialesInvalidas):
            srv.autenticar("operario", "mala")
    srv.autenticar("operario", "Oper123!")
    for _ in range(2):
        with pytest.raises(CredencialesInvalidas):
            srv.autenticar("operario", "mala")  # vuelve a contar desde cero: aún no bloquea


def test_cp_rf11_02_bitacora_sin_secretos_y_solo_para_admin(entorno):
    """CP-RF11-02: cada evento con usuario, IP y momento; ningún evento contiene la contraseña."""
    srv, auditoria, _, admin = entorno
    srv.autenticar("operario", "Oper123!", IP)
    with pytest.raises(CredencialesInvalidas):
        srv.autenticar("nadie", "x", IP)
    for _ in range(3):
        with pytest.raises((CredencialesInvalidas, CuentaBloqueada)):
            srv.autenticar("operario", "Secreta99", IP)
    with pytest.raises(CuentaBloqueada):
        srv.autenticar("operario", "Oper123!", IP)
    eventos = auditoria.listar(admin)
    assert [e.tipo for e in eventos] == [
        TipoEvento.LOGIN_RECHAZADO_BLOQUEO,
        TipoEvento.CUENTA_BLOQUEADA,
        TipoEvento.LOGIN_FALLIDO,
        TipoEvento.LOGIN_FALLIDO,
        TipoEvento.LOGIN_FALLIDO,
        TipoEvento.LOGIN_FALLIDO,
        TipoEvento.LOGIN_EXITOSO,
    ]
    assert all(e.ip == IP and e.momento and e.nombre_usuario for e in eventos)
    assert not any("Secreta99" in e.detalle or "Oper123!" in e.detalle for e in eventos)
    assert eventos[0].descripcion == "Intento con la cuenta bloqueada"
    with pytest.raises(PermisoDenegado):
        auditoria.listar(Usuario("o", "O", "h", Rol.PISCICULTOR, RelojFijo().ahora(), id=9))
    assert len(auditoria.listar(admin, limite=2)) == 2
