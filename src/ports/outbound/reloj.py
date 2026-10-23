"""Puerto de salida: fuente de fecha y hora (permite pruebas deterministas)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Reloj(Protocol):
    def ahora(self) -> datetime:
        """Fecha y hora actual en UTC con zona horaria."""
        ...
