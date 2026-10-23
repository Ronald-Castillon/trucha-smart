"""Esquemas Pydantic de la API (solo en el adaptador REST)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.model.alerta import Alerta, EstadoAlerta
from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua, Parametro
from src.domain.model.lote import Lote
from src.domain.model.registro_alimentacion import RegistroAlimentacion
from src.domain.model.registro_mortalidad import RegistroMortalidad
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Rol, Usuario
from src.domain.service.calculadora_fcr import ResumenProduccion
from src.domain.service.evaluador_calidad_agua import Evaluacion
from src.domain.service.indice_riesgo import IndiceRiesgo, Semaforo
from src.ports.inbound.consultar_historial import Historial
from src.ports.inbound.recomendar_racion import RecomendacionLote

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


# --------------------------------------------------------------------------- historial y riesgo


class RiesgoSalida(BaseModel):
    valor: int = Field(ge=0, le=100)
    semaforo: Semaforo
    nivel: str = Field(description="bajo | medio | alto")
    parametros_criticos: int
    parametros_precaucion: int
    alertas_criticas_abiertas: int
    formula: str

    @classmethod
    def de(cls, r: IndiceRiesgo) -> RiesgoSalida:
        return cls(
            valor=r.valor,
            semaforo=r.semaforo,
            nivel=r.nivel,
            parametros_criticos=r.parametros_criticos,
            parametros_precaucion=r.parametros_precaucion,
            alertas_criticas_abiertas=r.alertas_criticas_abiertas,
            formula=r.formula,
        )


class LecturaHistorial(LecturaSalida):
    niveles: dict[Parametro, Nivel]


class EstadisticaSalida(BaseModel):
    minimo: float
    maximo: float
    promedio: float


class HistorialSalida(BaseModel):
    estanque_id: int
    estanque: str
    desde: date
    hasta: date
    total: int
    lecturas: list[LecturaHistorial]
    estadisticas: dict[Parametro, EstadisticaSalida]

    @classmethod
    def de(cls, h: Historial) -> HistorialSalida:
        return cls(
            estanque_id=h.estanque.id,
            estanque=h.estanque.nombre,
            desde=h.desde,
            hasta=h.hasta,
            total=len(h.lecturas),
            lecturas=[
                LecturaHistorial(**LecturaSalida.de(x.lectura).model_dump(), niveles=x.niveles)
                for x in h.lecturas
            ],
            estadisticas={
                p: EstadisticaSalida(minimo=e.minimo, maximo=e.maximo, promedio=e.promedio)
                for p, e in h.estadisticas.items()
            },
        )


# --------------------------------------------------------------------------- alertas


class AlertaSalida(BaseModel):
    id: int
    estanque_id: int
    lectura_id: int
    parametro: Parametro
    nivel: Nivel
    valor: float
    mensaje: str
    estado: EstadoAlerta
    creada_en: datetime
    atendida_por: int | None
    atendida_en: datetime | None
    observacion: str | None

    @classmethod
    def de(cls, a: Alerta) -> AlertaSalida:
        return cls(**{k: getattr(a, k) for k in cls.model_fields})


class AtencionEntrada(BaseModel):
    observacion: str | None = Field(default=None, examples=["Se encendió el aireador"])


class EvaluacionSalida(BaseModel):
    parametro: Parametro
    valor: float
    nivel: Nivel
    mensaje: str

    @classmethod
    def de(cls, e: Evaluacion) -> EvaluacionSalida:
        return cls(parametro=e.parametro, valor=e.valor, nivel=e.nivel, mensaje=e.mensaje)


class LecturaRegistradaSalida(LecturaSalida):
    """Lectura guardada + evaluación contra umbrales + alertas creadas (RF-04)."""

    evaluacion: list[EvaluacionSalida]
    alertas: list[AlertaSalida]


class EstadoEstanque(BaseModel):
    """Resumen de un estanque para el panel (se refresca cada 1 s)."""

    estanque_id: int
    nombre: str
    ultima_lectura: LecturaSalida | None
    niveles: dict[Parametro, Nivel]
    alertas_abiertas: list[AlertaSalida]
    riesgo: RiesgoSalida


# ------------------------------------------------------------------- alimentación y producción


class AlimentacionEntrada(BaseModel):
    cantidad_kg: float = Field(examples=[25.5], description="kg de alimento (> 0)")
    registrado_en: datetime | None = Field(default=None, description="Por defecto, ahora")


class AlimentacionSalida(BaseModel):
    id: int
    lote_id: int
    cantidad_kg: float
    registrado_por: int | None
    registrado_en: datetime

    @classmethod
    def de(cls, r: RegistroAlimentacion) -> AlimentacionSalida:
        return cls(**{k: getattr(r, k) for k in cls.model_fields})


class MortalidadEntrada(BaseModel):
    cantidad: int = Field(examples=[12], description="n.º de peces muertos (> 0)")
    causa: str | None = Field(default=None, examples=["Manipulación en biometría"])
    registrado_en: datetime | None = None


class MortalidadSalida(BaseModel):
    id: int
    lote_id: int
    cantidad: int
    causa: str | None
    registrado_por: int | None
    registrado_en: datetime

    @classmethod
    def de(cls, r: RegistroMortalidad) -> MortalidadSalida:
        return cls(**{k: getattr(r, k) for k in cls.model_fields})


class ProduccionSalida(BaseModel):
    lote_id: int
    codigo: str
    peces_sembrados: int
    mortalidad_total: int
    peces_vivos: int
    supervivencia_pct: float
    peso_medio_inicial_g: float
    peso_medio_actual_g: float
    biomasa_inicial_kg: float
    biomasa_kg: float
    ganancia_biomasa_kg: float
    alimento_total_kg: float
    fcr: float | None = Field(description="null cuando no es calculable")
    fcr_texto: str
    fcr_detalle: str

    @classmethod
    def de(cls, r: ResumenProduccion) -> ProduccionSalida:
        datos = {k: getattr(r, k) for k in cls.model_fields}
        return cls(**datos)


# ------------------------------------------------------------------- ración


class RacionSalida(BaseModel):
    lote_id: int
    codigo: str
    peces_vivos: int
    biomasa_kg: float
    peso_medio_g: float
    tasa_pct: float
    tramo: str
    lectura_id: int | None = Field(description="Lectura de agua usada para los factores")
    nivel_temperatura: Nivel | None
    nivel_oxigeno: Nivel | None
    factor_temperatura: float
    factor_oxigeno: float
    racion_kg: float = Field(description="kg de alimento por día")
    suspender: bool
    regla: str
    advertencias: list[str]

    @classmethod
    def de(cls, r: RecomendacionLote) -> RacionSalida:
        rec = r.recomendacion
        return cls(
            lote_id=r.lote.id,
            codigo=r.lote.codigo,
            peces_vivos=r.peces_vivos,
            biomasa_kg=rec.biomasa_kg,
            peso_medio_g=rec.peso_medio_g,
            tasa_pct=rec.tasa_pct,
            tramo=rec.tramo,
            lectura_id=r.lectura.id if r.lectura else None,
            nivel_temperatura=rec.nivel_temperatura,
            nivel_oxigeno=rec.nivel_oxigeno,
            factor_temperatura=rec.factor_temperatura,
            factor_oxigeno=rec.factor_oxigeno,
            racion_kg=rec.racion_kg,
            suspender=rec.suspender,
            regla=rec.regla,
            advertencias=list(rec.advertencias),
        )
