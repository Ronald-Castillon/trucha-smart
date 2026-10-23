"""Adaptador del puerto Notificador que escribe las alertas en el log de la aplicación.

Es el canal del Incremento 1: la alerta queda visible en el panel (consulta cada 2 s) y en el
log del servidor. Correo/SMS/MQTT serían otros adaptadores del mismo puerto.
"""

from __future__ import annotations

import logging

from src.domain.model.alerta import Alerta

registro = logging.getLogger("truchasmart.alertas")


class NotificadorLog:
    def __init__(self) -> None:
        self.enviadas: list[Alerta] = []

    def notificar(self, alerta: Alerta) -> None:
        self.enviadas.append(alerta)
        registro.warning(
            "ALERTA %s · estanque %s · %s", alerta.nivel.value, alerta.estanque_id, alerta.mensaje
        )
