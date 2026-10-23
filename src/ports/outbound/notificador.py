"""Puerto de salida: aviso de alertas nuevas (registro, correo, SMS... según el adaptador)."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.alerta import Alerta


class Notificador(Protocol):
    def notificar(self, alerta: Alerta) -> None: ...
