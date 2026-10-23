"""Lote de peces sembrado en un estanque (RF-02). Un estanque tiene un único lote activo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.errores import Conflicto, ErrorValidacion


def _validar_positivo(campo: str, valor: float, descripcion: str) -> None:
    if valor is None or valor <= 0:
        raise ErrorValidacion(campo, f"{descripcion} debe ser mayor que 0")


@dataclass
class Lote:
    estanque_id: int
    codigo: str
    num_peces_inicial: int
    peso_medio_inicial_g: float
    peso_medio_actual_g: float
    fecha_siembra: date
    activo: bool = True
    fecha_cierre: date | None = None
    id: int | None = None

    @classmethod
    def sembrar(
        cls,
        estanque_id: int,
        codigo: str,
        num_peces: int,
        peso_medio_g: float,
        fecha_siembra: date,
        hoy: date,
    ) -> Lote:
        codigo = codigo.strip()
        if not (1 <= len(codigo) <= 40):
            raise ErrorValidacion("codigo", "El código del lote es obligatorio (máx. 40)")
        _validar_positivo("num_peces", num_peces, "El número de peces")
        _validar_positivo("peso_medio_g", peso_medio_g, "El peso medio")
        if fecha_siembra > hoy:
            raise ErrorValidacion("fecha_siembra", "La fecha de siembra no puede ser futura")
        return cls(
            estanque_id=estanque_id,
            codigo=codigo,
            num_peces_inicial=num_peces,
            peso_medio_inicial_g=peso_medio_g,
            peso_medio_actual_g=peso_medio_g,
            fecha_siembra=fecha_siembra,
        )

    def actualizar_peso(self, peso_medio_g: float) -> None:
        """Registra el peso medio de la última biometría (muestreo)."""
        self._exigir_activo()
        _validar_positivo("peso_medio_g", peso_medio_g, "El peso medio")
        self.peso_medio_actual_g = peso_medio_g

    def cerrar(self, fecha: date) -> None:
        """Cierra el lote (cosecha o traslado); el estanque queda libre para otro lote."""
        self._exigir_activo()
        if fecha < self.fecha_siembra:
            raise ErrorValidacion("fecha_cierre", "La fecha de cierre es anterior a la siembra")
        self.activo = False
        self.fecha_cierre = fecha

    def _exigir_activo(self) -> None:
        if not self.activo:
            raise Conflicto(f"El lote {self.codigo} está cerrado")
