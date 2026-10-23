"""Esquemas Pydantic de la API (solo en el adaptador REST)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua
from src.domain.model.lote import Lote
from src.domain.model.usuario import Rol, Usuario

# --------------------------------------------------------------------------- usuarios


class LoginEntrada(BaseModel):
    nombre_usuario: str = Field(examples=["operario"])
    password: str = Field(examples=["Oper123!"])


class UsuarioSalida(BaseModel):
    id: int
    nombre_usuario: str
    nombre_completo: str
    rol: Rol
    activo: bool
    creado_en: datetime

    @classmethod
    def de(cls, u: Usuario) -> UsuarioSalida:
        return cls(
            id=u.id,
            nombre_usuario=u.nombre_usuario,
            nombre_completo=u.nombre_completo,
            rol=u.rol,
            activo=u.activo,
            creado_en=u.creado_en,
        )


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en_segundos: int
    usuario: UsuarioSalida


class UsuarioEntrada(BaseModel):
    nombre_usuario: str
    nombre_completo: str
    password: str
    rol: Rol


# --------------------------------------------------------------------------- estanques y lotes


class EstanqueEntrada(BaseModel):
    nombre: str = Field(examples=["Estanque B1"])
    tipo: TipoEstanque = TipoEstanque.ESTANQUE
    volumen_m3: float | None = Field(default=None, examples=[120.0])
    ubicacion: str | None = Field(default=None, examples=["Sector sur"])


class LoteSalida(BaseModel):
    id: int
    estanque_id: int
    codigo: str
    num_peces_inicial: int
    peso_medio_inicial_g: float
    peso_medio_actual_g: float
    fecha_siembra: date
    activo: bool
    fecha_cierre: date | None

    @classmethod
    def de(cls, lo: Lote) -> LoteSalida:
        return cls(**{k: getattr(lo, k) for k in cls.model_fields})


class EstanqueSalida(BaseModel):
    id: int
    nombre: str
    tipo: TipoEstanque
    volumen_m3: float | None
    ubicacion: str | None
    activo: bool
    creado_en: datetime
    lote_activo: LoteSalida | None = None

    @classmethod
    def de(cls, e: Estanque, lote: Lote | None = None) -> EstanqueSalida:
        return cls(
            id=e.id,
            nombre=e.nombre,
            tipo=e.tipo,
            volumen_m3=e.volumen_m3,
            ubicacion=e.ubicacion,
            activo=e.activo,
            creado_en=e.creado_en,
            lote_activo=LoteSalida.de(lote) if lote else None,
        )


class LoteEntrada(BaseModel):
    codigo: str = Field(examples=["L-2026-10"])
    num_peces: int = Field(examples=[5000], description="Debe ser mayor que 0")
    peso_medio_g: float = Field(examples=[12.5], description="Debe ser mayor que 0")
    fecha_siembra: date


class PesoEntrada(BaseModel):
    peso_medio_g: float = Field(examples=[85.0], description="Peso medio de la biometría")


class CierreEntrada(BaseModel):
    fecha_cierre: date


# --------------------------------------------------------------------------- lecturas


class LecturaEntrada(BaseModel):
    estanque_id: int = Field(examples=[1])
    temperatura_c: float = Field(examples=[12.8], description="0 a 40 °C")
    oxigeno_mg_l: float = Field(examples=[8.1], description=">= 0 mg/L")
    ph: float = Field(examples=[7.4], description="0 a 14")
    fuente: FuenteLectura = FuenteLectura.SENSOR
    medido_en: datetime | None = Field(
        default=None, description="Fecha/hora ISO 8601 con zona horaria; por defecto, ahora"
    )


class LecturaSalida(BaseModel):
    id: int
    estanque_id: int
    temperatura_c: float
    oxigeno_mg_l: float
    ph: float
    fuente: FuenteLectura
    registrado_por: int | None
    medido_en: datetime

    @classmethod
    def de(cls, lec: LecturaAgua) -> LecturaSalida:
        return cls(**{k: getattr(lec, k) for k in cls.model_fields})


class EstadoEstanque(BaseModel):
    """Resumen de un estanque para el panel (se refresca cada 2 s)."""

    estanque_id: int
    nombre: str
    ultima_lectura: LecturaSalida | None
