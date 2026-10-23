"""Adaptador del puerto RepositorioUsuario con SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.outbound.persistence.orm import UsuarioORM
from src.domain.model.usuario import Rol, Usuario


def _a_dominio(f: UsuarioORM) -> Usuario:
    return Usuario(
        id=f.id,
        nombre_usuario=f.nombre_usuario,
        nombre_completo=f.nombre_completo,
        password_hash=f.password_hash,
        rol=Rol(f.rol),
        activo=f.activo,
        creado_en=f.creado_en,
    )


class RepositorioUsuarioSQL:
    def __init__(self, sesion: Session) -> None:
        self._s = sesion

    def guardar(self, usuario: Usuario) -> Usuario:
        fila = self._s.get(UsuarioORM, usuario.id) if usuario.id else None
        if fila is None:
            fila = UsuarioORM()
            self._s.add(fila)
        fila.nombre_usuario = usuario.nombre_usuario
        fila.nombre_completo = usuario.nombre_completo
        fila.password_hash = usuario.password_hash
        fila.rol = usuario.rol.value
        fila.activo = usuario.activo
        fila.creado_en = usuario.creado_en
        self._s.flush()
        return _a_dominio(fila)

    def por_id(self, usuario_id: int) -> Usuario | None:
        fila = self._s.get(UsuarioORM, usuario_id)
        return _a_dominio(fila) if fila else None

    def por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        fila = self._s.scalar(select(UsuarioORM).where(UsuarioORM.nombre_usuario == nombre_usuario))
        return _a_dominio(fila) if fila else None

    def listar(self) -> list[Usuario]:
        return [_a_dominio(f) for f in self._s.scalars(select(UsuarioORM).order_by(UsuarioORM.id))]
