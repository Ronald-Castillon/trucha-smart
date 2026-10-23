"""RF-01: usuarios, roles, permisos y autenticación (dominio)."""

import pytest

from src.domain.errores import Conflicto, CredencialesInvalidas, ErrorValidacion, PermisoDenegado
from src.domain.model.usuario import Permiso, Rol, Usuario
from src.domain.service.servicio_usuarios import ServicioUsuarios
from src.ports.inbound.registrar_usuario import ComandoRegistrarUsuario
from tests.fakes import HasherFalso, RelojFijo, RepositorioUsuarioMemoria


def _usuario(rol: Rol, activo: bool = True) -> Usuario:
    return Usuario("u", "U", "hash:x", rol, RelojFijo().ahora(), activo=activo, id=99)


@pytest.fixture
def servicio():
    repo = RepositorioUsuarioMemoria()
    srv = ServicioUsuarios(repo, HasherFalso(), RelojFijo())
    repo.guardar(Usuario("operario", "Olga", "hash:Oper123!", Rol.OPERARIO, RelojFijo().ahora()))
    return srv


@pytest.mark.parametrize(
    ("rol", "permitidos", "negados"),
    [
        (
            Rol.OPERARIO,
            {Permiso.REGISTRAR_LECTURA, Permiso.REGISTRAR_ALIMENTACION, Permiso.ATENDER_ALERTA},
            {Permiso.GESTIONAR_ESTANQUES, Permiso.GESTIONAR_REPORTES, Permiso.GESTIONAR_USUARIOS},
        ),
        (
            Rol.PISCICULTOR,
            {Permiso.REGISTRAR_LECTURA, Permiso.GESTIONAR_ESTANQUES, Permiso.GESTIONAR_REPORTES},
            {Permiso.GESTIONAR_USUARIOS},
        ),
        (Rol.ADMINISTRADOR, set(Permiso), set()),
    ],
)
def test_matriz_de_permisos_por_rol(rol, permitidos, negados):
    u = _usuario(rol)
    assert all(u.puede(p) for p in permitidos)
    assert not any(u.puede(p) for p in negados)


def test_usuario_inactivo_no_tiene_permisos():
    assert not _usuario(Rol.ADMINISTRADOR, activo=False).puede(Permiso.CONSULTAR)


def test_exigir_lanza_permiso_denegado():
    with pytest.raises(PermisoDenegado):
        _usuario(Rol.OPERARIO).exigir(Permiso.GESTIONAR_USUARIOS)


def test_cp_rf01_01_autenticar_con_credenciales_correctas(servicio):
    """CP-RF01-01: credenciales correctas devuelven el usuario con su rol."""
    u = servicio.autenticar(" Operario ", "Oper123!")
    assert u.nombre_usuario == "operario" and u.rol is Rol.OPERARIO


@pytest.mark.parametrize(("usuario", "password"), [("operario", "mala"), ("nadie", "Oper123!")])
def test_cp_rf01_02_credenciales_invalidas(servicio, usuario, password):
    """CP-RF01-02: contraseña incorrecta o usuario inexistente -> CredencialesInvalidas."""
    with pytest.raises(CredencialesInvalidas, match="Usuario o contraseña incorrectos"):
        servicio.autenticar(usuario, password)


def test_usuario_inactivo_no_puede_autenticarse(servicio):
    u = servicio._repo.por_nombre_usuario("operario")
    u.activo = False
    servicio._repo.guardar(u)
    with pytest.raises(CredencialesInvalidas):
        servicio.autenticar("operario", "Oper123!")
    assert servicio.usuario_activo(u.id) is None


def test_admin_registra_usuario_con_hash(servicio):
    nuevo = servicio.registrar(
        ComandoRegistrarUsuario("Pedro.P", " Pedro Pérez ", "Secreta123", Rol.PISCICULTOR),
        _usuario(Rol.ADMINISTRADOR),
    )
    assert nuevo.id is not None and nuevo.nombre_usuario == "pedro.p"
    assert nuevo.nombre_completo == "Pedro Pérez" and nuevo.password_hash == "hash:Secreta123"
    assert servicio.usuario_activo(nuevo.id) == nuevo
    assert len(servicio.listar(_usuario(Rol.ADMINISTRADOR))) == 2


def test_solo_admin_registra_usuarios(servicio):
    with pytest.raises(PermisoDenegado):
        servicio.registrar(
            ComandoRegistrarUsuario("x123", "X", "Secreta123", Rol.OPERARIO),
            _usuario(Rol.PISCICULTOR),
        )


@pytest.mark.parametrize(
    ("comando", "campo"),
    [
        (ComandoRegistrarUsuario("ab", "A", "Secreta123", Rol.OPERARIO), "nombre_usuario"),
        (
            ComandoRegistrarUsuario("con espacio", "A", "Secreta123", Rol.OPERARIO),
            "nombre_usuario",
        ),
        (ComandoRegistrarUsuario("valido", "A", "corta", Rol.OPERARIO), "password"),
        (ComandoRegistrarUsuario("valido", "  ", "Secreta123", Rol.OPERARIO), "nombre_completo"),
    ],
)
def test_validaciones_de_registro(servicio, comando, campo):
    with pytest.raises(ErrorValidacion) as e:
        servicio.registrar(comando, _usuario(Rol.ADMINISTRADOR))
    assert e.value.campo == campo


def test_nombre_de_usuario_duplicado(servicio):
    with pytest.raises(Conflicto):
        servicio.registrar(
            ComandoRegistrarUsuario("OPERARIO", "Otro", "Secreta123", Rol.OPERARIO),
            _usuario(Rol.ADMINISTRADOR),
        )
