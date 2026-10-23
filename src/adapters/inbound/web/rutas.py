"""Vistas web (Jinja2). Usan los mismos casos de uso que la API REST."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from src.adapters.inbound.rest.dependencias import (
    COOKIE_SESION,
    Contenedor,
    contenedor,
    usuario_actual,
)
from src.adapters.inbound.web.plantillas import render
from src.domain.errores import CredencialesInvalidas, ErrorDominio
from src.domain.model.usuario import Rol, Usuario
from src.ports.inbound.registrar_usuario import ComandoRegistrarUsuario

router = APIRouter(include_in_schema=False)


def _redirigir(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


@router.get("/")
def inicio():
    return _redirigir("/panel")


@router.get("/login")
def login_form(request: Request):
    return render(request, "login.html")


@router.post("/login")
def login(
    request: Request,
    nombre_usuario: str = Form(...),
    password: str = Form(...),
    c: Contenedor = Depends(contenedor),
):
    try:
        usuario = c.usuarios.autenticar(nombre_usuario, password)
    except CredencialesInvalidas as e:
        return render(request, "login.html", 401, error=e.mensaje, nombre_usuario=nombre_usuario)
    respuesta = _redirigir("/panel")
    respuesta.set_cookie(
        COOKIE_SESION,
        c.recursos.tokens.emitir(usuario),
        max_age=c.recursos.tokens.expira_segundos,
        httponly=True,
        samesite="lax",
    )
    return respuesta


@router.post("/logout")
def logout():
    respuesta = _redirigir("/login")
    respuesta.delete_cookie(COOKIE_SESION)
    return respuesta


@router.get("/panel")
def panel(request: Request, usuario: Usuario = Depends(usuario_actual)):
    return render(request, "panel.html", usuario=usuario)


def _vista_usuarios(request, c: Contenedor, usuario: Usuario, estado=200, **extra):
    return render(
        request,
        "usuarios.html",
        estado,
        usuario=usuario,
        usuarios=c.usuarios.listar(usuario),
        roles=list(Rol),
        **extra,
    )


@router.get("/usuarios")
def usuarios(
    request: Request,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    return _vista_usuarios(request, c, usuario)


@router.post("/usuarios")
def registrar_usuario(
    request: Request,
    nombre_usuario: str = Form(...),
    nombre_completo: str = Form(...),
    password: str = Form(...),
    rol: Rol = Form(...),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    try:
        nuevo = c.usuarios.registrar(
            ComandoRegistrarUsuario(nombre_usuario, nombre_completo, password, rol), usuario
        )
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_usuarios(request, c, usuario, 422, error=e.mensaje)
    return _vista_usuarios(
        request, c, usuario, aviso=f"Usuario '{nuevo.nombre_usuario}' registrado"
    )
