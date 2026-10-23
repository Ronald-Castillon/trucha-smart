"""Casos de uso de usuarios: registrar_usuario y autenticar (RF-01)."""

from __future__ import annotations

from src.domain.errores import Conflicto, CredencialesInvalidas, ErrorValidacion
from src.domain.model.usuario import (
    Permiso,
    Usuario,
    validar_nombre_usuario,
    validar_password,
)
from src.ports.inbound.registrar_usuario import ComandoRegistrarUsuario
from src.ports.outbound.hasher_password import HasherPassword
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_usuario import RepositorioUsuario


class ServicioUsuarios:
    """Implementa los puertos de entrada RegistrarUsuario y Autenticar."""

    def __init__(self, repo: RepositorioUsuario, hasher: HasherPassword, reloj: Reloj) -> None:
        self._repo = repo
        self._hasher = hasher
        self._reloj = reloj

    # -- RegistrarUsuario --------------------------------------------------
    def registrar(self, comando: ComandoRegistrarUsuario, solicitante: Usuario) -> Usuario:
        solicitante.exigir(Permiso.GESTIONAR_USUARIOS)
        nombre = validar_nombre_usuario(comando.nombre_usuario)
        validar_password(comando.password)
        nombre_completo = comando.nombre_completo.strip()
        if not nombre_completo:
            raise ErrorValidacion("nombre_completo", "El nombre completo es obligatorio")
        if self._repo.por_nombre_usuario(nombre) is not None:
            raise Conflicto(f"El nombre de usuario '{nombre}' ya está registrado")
        usuario = Usuario(
            nombre_usuario=nombre,
            nombre_completo=nombre_completo,
            password_hash=self._hasher.hashear(comando.password),
            rol=comando.rol,
            creado_en=self._reloj.ahora(),
        )
        return self._repo.guardar(usuario)

    def listar(self, solicitante: Usuario) -> list[Usuario]:
        solicitante.exigir(Permiso.GESTIONAR_USUARIOS)
        return self._repo.listar()

    # -- Autenticar --------------------------------------------------------
    def autenticar(self, nombre_usuario: str, password: str) -> Usuario:
        usuario = self._repo.por_nombre_usuario(nombre_usuario.strip().lower())
        if (
            usuario is None
            or not usuario.activo
            or not self._hasher.verificar(password, usuario.password_hash)
        ):
            raise CredencialesInvalidas()
        return usuario

    def usuario_activo(self, usuario_id: int) -> Usuario | None:
        usuario = self._repo.por_id(usuario_id)
        return usuario if usuario is not None and usuario.activo else None
