"""Casos de uso de usuarios: registrar_usuario y autenticar (RF-01)."""

from __future__ import annotations

import math

from src.domain.errores import Conflicto, CredencialesInvalidas, CuentaBloqueada, ErrorValidacion
from src.domain.model.evento_seguridad import TipoEvento
from src.domain.model.usuario import (
    Permiso,
    Usuario,
    validar_nombre_usuario,
    validar_password,
)
from src.domain.service.servicio_auditoria import ServicioAuditoria
from src.ports.inbound.registrar_usuario import ComandoRegistrarUsuario
from src.ports.outbound.hasher_password import HasherPassword
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_usuario import RepositorioUsuario


class ServicioUsuarios:
    """Implementa los puertos de entrada RegistrarUsuario y Autenticar."""

    def __init__(
        self,
        repo: RepositorioUsuario,
        hasher: HasherPassword,
        reloj: Reloj,
        auditoria: ServicioAuditoria | None = None,
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._reloj = reloj
        self._auditoria = auditoria

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

    def nombres(self, solicitante: Usuario) -> dict[int, str]:
        """Nombre completo por id, para mostrar quién registró o atendió algo (B-04, B-06)."""
        solicitante.exigir(Permiso.CONSULTAR)
        return {u.id: u.nombre_completo for u in self._repo.listar()}

    # -- Autenticar --------------------------------------------------------
    def autenticar(self, nombre_usuario: str, password: str, ip: str | None = None) -> Usuario:
        """Tras MAXIMO_INTENTOS_FALLIDOS seguidos la cuenta queda bloqueada MINUTOS_BLOQUEO (RF-11).

        Los intentos fallidos y el bloqueo se guardan aunque se lance la excepción: el adaptador
        debe confirmar la transacción también en ese caso.
        """
        nombre = nombre_usuario.strip().lower()
        usuario = self._repo.por_nombre_usuario(nombre)
        ahora = self._reloj.ahora()
        if usuario is None or not usuario.activo:
            self._evento(
                TipoEvento.LOGIN_FALLIDO, nombre, None, ip, "usuario inexistente o inactivo"
            )
            raise CredencialesInvalidas()
        if usuario.bloqueado(ahora):
            self._evento(TipoEvento.LOGIN_RECHAZADO_BLOQUEO, nombre, usuario.id, ip)
            raise self._bloqueada(usuario, ahora)
        if not self._hasher.verificar(password, usuario.password_hash):
            se_bloqueo = usuario.registrar_fallo(ahora)
            self._repo.guardar(usuario)
            self._evento(TipoEvento.LOGIN_FALLIDO, nombre, usuario.id, ip, "contraseña incorrecta")
            if se_bloqueo:
                self._evento(TipoEvento.CUENTA_BLOQUEADA, nombre, usuario.id, ip)
                raise self._bloqueada(usuario, ahora)
            raise CredencialesInvalidas()
        if usuario.intentos_fallidos or usuario.bloqueado_hasta:
            usuario.registrar_exito()
            usuario = self._repo.guardar(usuario)
        self._evento(TipoEvento.LOGIN_EXITOSO, nombre, usuario.id, ip)
        return usuario

    @staticmethod
    def _bloqueada(usuario: Usuario, ahora) -> CuentaBloqueada:
        minutos = math.ceil((usuario.bloqueado_hasta - ahora).total_seconds() / 60)
        return CuentaBloqueada(
            f"Cuenta bloqueada por intentos fallidos. Intente de nuevo en {minutos} min "
            "o pida al Administrador que la revise."
        )

    def _evento(self, tipo, nombre, usuario_id, ip, detalle: str = "") -> None:
        if self._auditoria is not None:
            self._auditoria.registrar(tipo, nombre, usuario_id, ip, detalle)

    def usuario_activo(self, usuario_id: int) -> Usuario | None:
        usuario = self._repo.por_id(usuario_id)
        return usuario if usuario is not None and usuario.activo else None
