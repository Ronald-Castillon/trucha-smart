# Tarjeta del modelo `riesgo-v1` (RF-12, ADR-007)

Generada por `tools/entrenar_modelo_riesgo.py`; no se edita a mano.

## Uso previsto
Estimar la probabilidad de que un estanque llegue a condición crítica (OD < 5 mg/L o
temperatura > 18 °C) en las próximas 6 h, para priorizar revisiones. Es apoyo a la
decisión: no reemplaza las alertas por umbral ni el criterio del técnico.

## Datos
- **Sintéticos**: 1500 trayectorias de 36 h (semilla 2026) con
  ciclo diario, ruido y eventos de hipoxia, calentamiento y falsas alarmas.
- Entrenamiento: 7495 muestras; prueba: 2481 muestras de
  368 trayectorias no vistas (278 positivas).
- **Limitación**: no hay historial real etiquetado de la piscigranja. Las métricas miden
  qué tan bien el modelo aprende el generador sintético, no su desempeño en campo.

## Métricas en el conjunto de prueba

| Método | Precisión | Recall | F1 | AUC |
|---|---:|---:|---:|---:|
| Modelo, umbral 0.5 | 0.7903 | 0.5288 | 0.6336 | 0.898 |
| Modelo, umbral ALTO 0.6 | 0.8205 | 0.4604 | 0.5899 | — |
| Regla de tendencia del Inc. 3 (ADR-006) | 0.8966 | 0.0935 | 0.1694 | — |

## Coeficientes (características estandarizadas)

| Característica | Coeficiente |
|---|---:|
| `t_margen` | -1.592 |
| `od_margen` | -1.582 |
| `od_pendiente_6h` | -1.231 |
| `t_max_24h` | -0.979 |
| `t_pendiente_6h` | +0.611 |
| `od_min_24h` | +0.510 |
| `ph_actual` | +0.234 |
| intercepto | -3.313 |

## Antes de usarlo en producción
Reentrenar con lecturas reales etiquetadas (eventos críticos registrados en las alertas),
validar con el técnico de la piscigranja y comparar otra vez con la regla del Inc. 3.
