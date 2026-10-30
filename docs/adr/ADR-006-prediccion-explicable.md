# ADR-006: Predicción de tendencia explicable (regresión lineal) en el Incremento 3

- **Estado:** Aceptado
- **Fecha:** 2026-10-30
- **Relacionado:** ADR-005 (reglas parametrizables en lugar de ML), brecha B-10

## Contexto
ADR-005 dejó la predicción para el Incremento 3, "cuando haya datos históricos suficientes". El
sistema ya registra lecturas frecuentes (sensor simulado cada pocos segundos), pero todavía no hay
meses de historia real ni eventos etiquetados para entrenar un modelo de aprendizaje automático.
El usuario necesita anticiparse a la hipoxia y al calentamiento del agua, y la decisión sigue siendo
humana.

## Decisión
Implementar la predicción como **regresión lineal por mínimos cuadrados** de cada parámetro sobre
las lecturas de las **24 h previas a la última lectura** (mínimo 4 puntos), en el dominio
(`domain/service/predictor_tendencia.py`, solo biblioteca estándar). Si la recta avanza hacia el
límite crítico de `config/umbrales.yaml` y lo cruzaría en **6 h** o menos, con **R² ≥ 0.5**, se
informa el tiempo estimado, la hora y el ajuste. Si no, "sin riesgo previsto" o "datos
insuficientes".

## Consecuencias
- (+) Explicable: muestra la pendiente por hora y el R²; el piscicultor entiende por qué se avisa.
- (+) Se prueba con valores exactos (pruebas unitarias con rectas conocidas).
- (−) Solo capta tendencias lineales de corto plazo; no modela ciclos diarios ni efectos externos.
- (−) La brecha B-10 queda cubierta con analítica estadística, no con IA entrenada. Cuando haya
  historia suficiente, el puerto `predecir_tendencia` permite cambiar a un modelo de ML sin tocar
  la API ni la interfaz.

## Atributo de calidad
Explicabilidad, capacidad de prueba y evolucionabilidad (sustitución del algoritmo detrás de un puerto).
