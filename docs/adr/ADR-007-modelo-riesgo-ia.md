# ADR-007: Modelo de riesgo entrenado (regresión logística) detrás de un puerto, Incremento 4

- **Estado:** Aceptado
- **Fecha:** 2026-11-06
- **Relacionado:** ADR-005 (reglas en lugar de ML), ADR-006 (predicción explicable por regresión
  lineal), plan de incrementos de las Guías 2–4 (modelo predictivo en el Incremento 4), HU-12

## Contexto
ADR-006 dejó el puerto de predicción listo para cambiar el algoritmo «cuando haya historia
suficiente». El plan del equipo ubicaba el modelo predictivo de IA en el Incremento 4. La regla
lineal del Incremento 3 es explicable, pero detecta pocos eventos: sobre trayectorias con ciclo
diario y ruido su recall fue de 9 % (ver la tarjeta del modelo). Todavía **no existe historial real
etiquetado** de la piscigranja.

## Decisión
1. Entrenar una **regresión logística** (scikit-learn) que estima la probabilidad de evento
   crítico (OD < 5 mg/L o temperatura > 18 °C) en las próximas 6 h, con siete características de
   la ventana de 24 h calculadas **en el dominio** (`domain/service/riesgo_modelo.py`), de modo
   que entrenamiento e inferencia usan exactamente la misma función.
2. Entrenar con **datos sintéticos reproducibles** (`tools/entrenar_modelo_riesgo.py`, semilla
   fija), separando entrenamiento y prueba por trayectoria, y comparar contra la regla del Inc. 3.
3. Exportar el modelo a **JSON** (medias, escalas, coeficientes, intercepto) en
   `models/riesgo/modelo_v1.json` junto con su **tarjeta del modelo**. La inferencia la hace el
   adaptador `adapters/outbound/ml/modelo_logistico.py` sin scikit-learn y **sin pickle** (cargar
   un modelo nunca ejecuta código; Bandit sigue sin hallazgos).
4. El dominio solo conoce el puerto `ModeloRiesgo`; scikit-learn y numpy quedan prohibidos para
   dominio y puertos (contrato de import-linter).
5. CI reentrena y verifica que el resultado sea idéntico al archivo versionado y que su F1 supere
   al de la regla del Inc. 3 (CP-RF12-03).

## Consecuencias
- (+) Mejor detección que la regla lineal en los datos de prueba (F1 0.63 frente a 0.17; AUC 0.90).
- (+) Explicable: cada predicción informa los factores que más aportan (coeficiente × valor
  estandarizado) y la versión del modelo.
- (+) Reproducible y versionado (MLOps ligero): semilla, datos, métricas y modelo en Git.
- (−) **Prototipo**: las métricas miden cuánto aprende el generador sintético, no el desempeño en
  campo. Debe reentrenarse y validarse con lecturas y eventos reales antes de usarse para decidir.
- (−) Un modelo lineal no captura interacciones complejas; cuando haya datos reales se puede
  evaluar otro algoritmo detrás del mismo puerto.

## Atributo de calidad
Evolucionabilidad (algoritmo sustituible detrás de un puerto), explicabilidad, reproducibilidad y
seguridad (sin deserialización de código).
