"""Umbrales por defecto de config/umbrales.yaml expresados sin YAML (para pruebas de dominio)."""

from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import ConjuntoUmbrales, Umbral

UMBRALES = ConjuntoUmbrales(
    temperatura=Umbral(Parametro.TEMPERATURA, "°C", 10.0, 16.0, 8.0, 18.0),
    oxigeno_disuelto=Umbral(Parametro.OXIGENO_DISUELTO, "mg/L", 7.0, None, 5.0, None),
    ph=Umbral(Parametro.PH, "pH", 6.5, 8.5, 6.0, 9.0),
)
