"""Router de autenticación y gestión de usuarios (RF-01)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

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
from src.domain.errores import ErrorDominio
from src.domain.model.evento_seguridad import EventoSeguridad
from src.domain.model.usuario import Usuario
from src.ports.inbound.registrar_usuario import ComandoRegistrarUsuario

router = APIRouter(prefix="/api", responses=RESPUESTAS_ERROR)


def ip_cliente(request: Request) -> str | None:
    return request.client.host if request.client else None


def autenticar_y_registrar(c: Contenedor, nombre: str, password: str, request: Request) -> Usuario:
    """Confirma la transacción también si falla: el contador de intentos y la bitácora persisten."""
    try:
        usuario = c.usuarios.autenticar(nombre, password, ip_cliente(request))
    except ErrorDominio:
        c.confirmar()
        raise
    c.confirmar()
    return usuario


@router.post("/auth/login", response_model=TokenSalida, tags=["autenticación"])
def login(
    datos: LoginEntrada, request: Request, c: Contenedor = Depends(contenedor)
) -> TokenSalida:
    """Valida credenciales y devuelve un JWT para usar como `Authorization: Bearer`.

    Tras 3 intentos fallidos seguidos la cuenta queda bloqueada 5 minutos (423, RF-11).
    """
    usuario = autenticar_y_registrar(c, datos.nombre_usuario, datos.password, request)
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


class EventoSalida(BaseModel):
    id: int
    tipo: str
    descripcion: str
    momento: datetime
    nombre_usuario: str | None
    usuario_id: int | None
    ip: str | None
    detalle: str

    @classmethod
    def de(cls, e: EventoSeguridad) -> EventoSalida:
        return cls(
            id=e.id,
            tipo=e.tipo.value,
            descripcion=e.descripcion,
            momento=e.momento,
            nombre_usuario=e.nombre_usuario,
            usuario_id=e.usuario_id,
            ip=e.ip,
            detalle=e.detalle,
        )


@router.get("/auditoria", response_model=list[EventoSalida], tags=["auditoría"])
def auditoria(
    limite: int = 200,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> list[EventoSalida]:
    """Bitácora de seguridad (RF-11): inicios de sesión, bloqueos y claves. Solo Administrador."""
    return [EventoSalida.de(e) for e in c.auditoria.listar(usuario, limite)]
