"""Router de autenticación y gestión de usuarios (RF-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from src.adapters.inbound.rest.dependencias import (
    COOKIE_SESION,
    Contenedor,
    contenedor,
    usuario_actual,
)
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.rest.esquemas import (
    LoginEntrada,
    TokenSalida,
    UsuarioEntrada,
    UsuarioSalida,
)
from src.domain.model.usuario import Usuario
from src.ports.inbound.registrar_usuario import ComandoRegistrarUsuario

router = APIRouter(prefix="/api", responses=RESPUESTAS_ERROR)


@router.post("/auth/login", response_model=TokenSalida, tags=["autenticación"])
def login(datos: LoginEntrada, c: Contenedor = Depends(contenedor)) -> TokenSalida:
    """Valida credenciales y devuelve un JWT para usar como `Authorization: Bearer`."""
    usuario = c.usuarios.autenticar(datos.nombre_usuario, datos.password)
    tokens = c.recursos.tokens
    return TokenSalida(
        access_token=tokens.emitir(usuario),
        expira_en_segundos=tokens.expira_segundos,
        usuario=UsuarioSalida.de(usuario),
    )


@router.post("/auth/logout", status_code=204, tags=["autenticación"])
def logout(response: Response) -> Response:
    """Elimina la cookie de sesión web."""
    response.delete_cookie(COOKIE_SESION)
    response.status_code = 204
    return response


@router.get("/auth/yo", response_model=UsuarioSalida, tags=["autenticación"])
def yo(usuario: Usuario = Depends(usuario_actual)) -> UsuarioSalida:
    return UsuarioSalida.de(usuario)


@router.get("/usuarios", response_model=list[UsuarioSalida], tags=["usuarios"])
def listar_usuarios(
    usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> list[UsuarioSalida]:
    return [UsuarioSalida.de(u) for u in c.usuarios.listar(usuario)]


@router.post("/usuarios", response_model=UsuarioSalida, status_code=201, tags=["usuarios"])
def registrar_usuario(
    datos: UsuarioEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> UsuarioSalida:
    """Registra un usuario con su rol. Solo Administrador."""
    nuevo = c.usuarios.registrar(
        ComandoRegistrarUsuario(
            nombre_usuario=datos.nombre_usuario,
            nombre_completo=datos.nombre_completo,
            password=datos.password,
            rol=datos.rol,
        ),
        usuario,
    )
    c.confirmar()
    return UsuarioSalida.de(nuevo)
