"""Errores del dominio. Los adaptadores los traducen a códigos HTTP."""

from __future__ import annotations


class ErrorDominio(Exception):
    """Base de todos los errores de negocio."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ErrorValidacion(ErrorDominio):
    """Un dato no cumple una regla del negocio (HTTP 422)."""

    def __init__(self, campo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.campo = campo


class NoEncontrado(ErrorDominio):
    """El recurso solicitado no existe (HTTP 404)."""


class Conflicto(ErrorDominio):
    """La operación choca con el estado actual (HTTP 409)."""


class CredencialesInvalidas(ErrorDominio):
    """Usuario o contraseña incorrectos (HTTP 401)."""

    def __init__(self) -> None:
        super().__init__("Usuario o contraseña incorrectos")


class PermisoDenegado(ErrorDominio):
    """El rol del usuario no permite la acción (HTTP 403)."""
