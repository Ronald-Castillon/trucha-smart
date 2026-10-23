"""Vistas web (Jinja2). Usan los mismos casos de uso que la API REST."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from src.adapters.inbound.rest.dependencias import (
    COOKIE_SESION,
    Contenedor,
    contenedor,
    usuario_actual,
)
from src.adapters.inbound.web.plantillas import render
from src.domain.errores import CredencialesInvalidas, ErrorDominio, ErrorValidacion
from src.domain.model.alerta import EstadoAlerta
from src.domain.model.estanque import TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura
from src.domain.model.usuario import Rol, Usuario
from src.ports.inbound.gestionar_estanque import ComandoSembrarLote, DatosEstanque
from src.ports.inbound.registrar_lectura import ComandoRegistrarLectura
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


def _numero(campo: str, valor: str, tipo=float, opcional: bool = False):
    """Convierte un campo de formulario; los errores se informan con el nombre del campo."""
    valor = (valor or "").strip().replace(",", ".")
    if not valor:
        if opcional:
            return None
        raise ErrorValidacion(campo, f"El campo {campo} es obligatorio")
    try:
        return tipo(valor)
    except ValueError:
        raise ErrorValidacion(campo, f"El campo {campo} debe ser numérico") from None


def _fecha(campo: str, valor: str) -> date:
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ErrorValidacion(campo, f"El campo {campo} no es una fecha válida") from None


def _estanques_con_lote(c: Contenedor, usuario: Usuario):
    return [(e, c.estanques.lote_activo(e.id, usuario)) for e in c.estanques.listar(usuario)]


def _vista_panel(request, c: Contenedor, usuario: Usuario, **extra):
    filas = [
        (e, lote, c.lecturas.estado(e.id, usuario), c.historial.riesgo(e.id, usuario))
        for e, lote in _estanques_con_lote(c, usuario)
    ]
    return render(request, "panel.html", usuario=usuario, filas=filas, **extra)


@router.get("/panel")
def panel(
    request: Request,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    return _vista_panel(request, c, usuario)


# --------------------------------------------------------------------------- lecturas (RF-03)


def _vista_lectura(request, c: Contenedor, usuario: Usuario, estado=200, **extra):
    extra.setdefault("form", {})
    return render(
        request,
        "lectura_nueva.html",
        estado,
        usuario=usuario,
        estanques=c.estanques.listar(usuario),
        **extra,
    )


@router.get("/lecturas/nueva")
def lectura_nueva(
    request: Request,
    estanque_id: int | None = None,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    return _vista_lectura(request, c, usuario, form={"estanque_id": estanque_id or ""})


@router.post("/lecturas")
def registrar_lectura(
    request: Request,
    estanque_id: int = Form(...),
    temperatura_c: str = Form(""),
    oxigeno_mg_l: str = Form(""),
    ph: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    form = {
        "estanque_id": estanque_id,
        "temperatura_c": temperatura_c,
        "oxigeno_mg_l": oxigeno_mg_l,
        "ph": ph,
    }
    try:
        comando = ComandoRegistrarLectura(
            estanque_id=estanque_id,
            temperatura_c=_numero("temperatura_c", temperatura_c),
            oxigeno_mg_l=_numero("oxigeno_mg_l", oxigeno_mg_l),
            ph=_numero("ph", ph),
            fuente=FuenteLectura.MANUAL,
        )
        resultado = c.lecturas.registrar(comando, usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_lectura(request, c, usuario, 422, error=e.mensaje, form=form)
    aviso = "Lectura registrada"
    if resultado.alertas_nuevas:
        aviso += f" · {len(resultado.alertas_nuevas)} alerta(s) generada(s)"
    return _vista_panel(request, c, usuario, aviso=aviso)


# --------------------------------------------------------------------------- producción (RF-06)


def _vista_produccion(request, c: Contenedor, usuario: Usuario, lote_id: int, estado=200, **extra):
    lote = c.estanques.obtener_lote(lote_id, usuario)
    extra.setdefault("form", {})
    return render(
        request,
        "produccion.html",
        estado,
        usuario=usuario,
        lote=lote,
        estanque=c.estanques.obtener(lote.estanque_id, usuario),
        resumen=c.produccion.produccion(lote_id, usuario),
        racion=c.racion.recomendar(lote_id, usuario) if lote.activo else None,
        alimentaciones=c.produccion.alimentaciones(lote_id, usuario)[:15],
        mortalidades=c.produccion.mortalidades(lote_id, usuario)[:15],
        **extra,
    )


@router.get("/lotes/{lote_id}/produccion")
def produccion(
    request: Request,
    lote_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    return _vista_produccion(request, c, usuario, lote_id)


@router.post("/lotes/{lote_id}/alimentacion")
def registrar_alimentacion(
    request: Request,
    lote_id: int,
    cantidad_kg: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    try:
        cantidad = _numero("cantidad_kg", cantidad_kg)
        c.produccion.registrar_alimentacion(lote_id, cantidad, usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_produccion(
            request, c, usuario, lote_id, 422, error=e.mensaje, form={"cantidad_kg": cantidad_kg}
        )
    return _vista_produccion(
        request, c, usuario, lote_id, aviso=f"Alimentación de {cantidad:g} kg registrada"
    )


@router.post("/lotes/{lote_id}/mortalidad")
def registrar_mortalidad(
    request: Request,
    lote_id: int,
    cantidad: str = Form(""),
    causa: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    try:
        n = _numero("cantidad", cantidad, int)
        c.produccion.registrar_mortalidad(lote_id, n, causa, usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_produccion(
            request,
            c,
            usuario,
            lote_id,
            422,
            error=e.mensaje,
            form={"cantidad": cantidad, "causa": causa},
        )
    return _vista_produccion(
        request, c, usuario, lote_id, aviso=f"Mortalidad de {n} peces registrada"
    )


# --------------------------------------------------------------------------- historial (RF-05)


@router.get("/estanques/{estanque_id}/historial")
def historial(
    request: Request,
    estanque_id: int,
    desde: str = "",
    hasta: str = "",
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    error = None
    try:
        h = c.historial.historial(
            estanque_id,
            usuario,
            _fecha("desde", desde) if desde else None,
            _fecha("hasta", hasta) if hasta else None,
        )
    except ErrorValidacion as e:
        error = e.mensaje
        h = c.historial.historial(estanque_id, usuario)
    serie = [
        {
            "t": x.lectura.medido_en.strftime("%d/%m %H:%M"),
            "temperatura": x.lectura.temperatura_c,
            "oxigeno": x.lectura.oxigeno_mg_l,
            "ph": x.lectura.ph,
        }
        for x in h.lecturas
    ]
    return render(
        request,
        "historial.html",
        422 if error else 200,
        usuario=usuario,
        h=h,
        serie=serie,
        riesgo=c.historial.riesgo(estanque_id, usuario),
        error=error,
    )


# --------------------------------------------------------------------------- alertas (RF-04)


def _vista_alertas(request, c: Contenedor, usuario: Usuario, estado=200, **extra):
    return render(
        request,
        "alertas.html",
        estado,
        usuario=usuario,
        abiertas=c.alertas.listar(usuario, estado=EstadoAlerta.ABIERTA),
        atendidas=c.alertas.listar(usuario, estado=EstadoAlerta.ATENDIDA, limite=30),
        nombres={e.id: e.nombre for e in c.repo_estanques.listar(solo_activos=False)},
        usuarios=c.usuarios.nombres(usuario),
        **extra,
    )


@router.get("/alertas")
def alertas(
    request: Request,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    return _vista_alertas(request, c, usuario)


@router.post("/alertas/{alerta_id}/atender")
def atender_alerta(
    request: Request,
    alerta_id: int,
    observacion: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    try:
        c.alertas.atender(alerta_id, observacion, usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_alertas(request, c, usuario, 409, error=e.mensaje)
    return _vista_alertas(request, c, usuario, aviso=f"Alerta {alerta_id} atendida")


# --------------------------------------------------------------------------- estanques (RF-02)


def _vista_estanques(request, c: Contenedor, usuario: Usuario, estado=200, **extra):
    extra.setdefault("form", {})
    return render(
        request,
        "estanques.html",
        estado,
        usuario=usuario,
        filas=_estanques_con_lote(c, usuario),
        **extra,
    )


@router.get("/estanques")
def estanques(
    request: Request,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    return _vista_estanques(request, c, usuario)


@router.post("/estanques")
def crear_estanque(
    request: Request,
    nombre: str = Form(""),
    tipo: TipoEstanque = Form(TipoEstanque.ESTANQUE),
    volumen_m3: str = Form(""),
    ubicacion: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    form = {"nombre": nombre, "tipo": tipo.value, "volumen_m3": volumen_m3, "ubicacion": ubicacion}
    try:
        datos = DatosEstanque(
            nombre, tipo, _numero("volumen_m3", volumen_m3, opcional=True), ubicacion or None
        )
        nuevo = c.estanques.crear(datos, usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_estanques(request, c, usuario, 422, error=e.mensaje, form=form)
    return _vista_estanques(request, c, usuario, aviso=f"Estanque {nuevo.nombre} creado")


def _vista_detalle(request, c: Contenedor, usuario: Usuario, estanque_id: int, estado=200, **extra):
    extra.setdefault("form", {})
    return render(
        request,
        "estanque_detalle.html",
        estado,
        usuario=usuario,
        estanque=c.estanques.obtener(estanque_id, usuario),
        lote=c.estanques.lote_activo(estanque_id, usuario),
        lotes=c.estanques.lotes_de(estanque_id, usuario),
        hoy=c.recursos.reloj.ahora().date().isoformat(),
        **extra,
    )


@router.get("/estanques/{estanque_id}")
def detalle_estanque(
    request: Request,
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    return _vista_detalle(request, c, usuario, estanque_id)


@router.post("/estanques/{estanque_id}")
def actualizar_estanque(
    request: Request,
    estanque_id: int,
    nombre: str = Form(""),
    tipo: TipoEstanque = Form(TipoEstanque.ESTANQUE),
    volumen_m3: str = Form(""),
    ubicacion: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    try:
        datos = DatosEstanque(
            nombre, tipo, _numero("volumen_m3", volumen_m3, opcional=True), ubicacion or None
        )
        c.estanques.actualizar(estanque_id, datos, usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_detalle(request, c, usuario, estanque_id, 422, error=e.mensaje)
    return _vista_detalle(request, c, usuario, estanque_id, aviso="Cambios guardados")


@router.post("/estanques/{estanque_id}/baja")
def baja_estanque(
    request: Request,
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    try:
        c.estanques.desactivar(estanque_id, usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_detalle(request, c, usuario, estanque_id, 409, error=e.mensaje)
    return _vista_estanques(request, c, usuario, aviso="Estanque dado de baja")


@router.post("/estanques/{estanque_id}/lotes")
def sembrar_lote(
    request: Request,
    estanque_id: int,
    codigo: str = Form(""),
    num_peces: str = Form(""),
    peso_medio_g: str = Form(""),
    fecha_siembra: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    form = {
        "codigo": codigo,
        "num_peces": num_peces,
        "peso_medio_g": peso_medio_g,
        "fecha_siembra": fecha_siembra,
    }
    try:
        comando = ComandoSembrarLote(
            estanque_id,
            codigo,
            _numero("num_peces", num_peces, int),
            _numero("peso_medio_g", peso_medio_g),
            _fecha("fecha_siembra", fecha_siembra),
        )
        lote = c.estanques.sembrar_lote(comando, usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_detalle(request, c, usuario, estanque_id, 422, error=e.mensaje, form=form)
    return _vista_detalle(request, c, usuario, estanque_id, aviso=f"Lote {lote.codigo} sembrado")


@router.post("/lotes/{lote_id}/peso")
def actualizar_peso(
    request: Request,
    lote_id: int,
    peso_medio_g: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    lote = c.estanques.obtener_lote(lote_id, usuario)
    try:
        c.estanques.actualizar_peso(lote_id, _numero("peso_medio_g", peso_medio_g), usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_detalle(request, c, usuario, lote.estanque_id, 422, error=e.mensaje)
    return _vista_detalle(request, c, usuario, lote.estanque_id, aviso="Peso medio actualizado")


@router.post("/lotes/{lote_id}/cerrar")
def cerrar_lote(
    request: Request,
    lote_id: int,
    fecha_cierre: str = Form(""),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
):
    lote = c.estanques.obtener_lote(lote_id, usuario)
    try:
        c.estanques.cerrar_lote(lote_id, _fecha("fecha_cierre", fecha_cierre), usuario)
        c.confirmar()
    except ErrorDominio as e:
        c.sesion.rollback()
        return _vista_detalle(request, c, usuario, lote.estanque_id, 422, error=e.mensaje)
    return _vista_detalle(
        request, c, usuario, lote.estanque_id, aviso=f"Lote {lote.codigo} cerrado"
    )


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
