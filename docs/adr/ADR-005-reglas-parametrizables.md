# ADR-005: Reglas parametrizables en lugar de aprendizaje automático

- **Estado:** Aceptado
- **Fecha:** 2026-10-23

## Contexto
No existe historial digital (B-01, B-07) para entrenar modelos. Los umbrales hoy no están
estandarizados (B-05) y las decisiones deben seguir siendo humanas y explicables.

## Decisión
Implementar evaluación de calidad de agua, índice de riesgo y recomendación de ración como reglas
deterministas en el dominio, con parámetros externos en `config/umbrales.yaml` y
`config/alimentacion.yaml` (valores de referencia a validar con el técnico de la piscigranja).
La recomendación muestra la regla aplicada. La predicción con IA (B-10) queda para el Incremento 3,
cuando haya datos históricos suficientes.

## Consecuencias
- (+) Resultados explicables y verificables con pruebas de valores límite.
- (+) El técnico ajusta parámetros sin cambiar código.
- (−) No anticipa eventos; B-10 queda abierta y se refleja en M3.1.

## Atributo de calidad
Explicabilidad/transparencia, mantenibilidad, corrección funcional.
