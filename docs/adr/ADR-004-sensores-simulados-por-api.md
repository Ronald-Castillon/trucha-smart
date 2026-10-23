# ADR-004: Sensores simulados que envían lecturas por la API REST

- **Estado:** Aceptado
- **Fecha:** 2026-10-23

## Contexto
No se dispone de sondas IoT en la piscigranja durante el curso. B-02 (mediciones esporádicas)
requiere demostrar ingreso frecuente y automático de lecturas.

## Decisión
Implementar un simulador (`python -m src.adapters.inbound.simulator`) con escenarios
`normal`, `critico_oxigeno` y `critico_temperatura` que publica lecturas en `POST /api/lecturas`
autenticándose con JWT Bearer. El protocolo MQTT y sensores reales se posponen al Incremento 3.

## Consecuencias
- (+) Se ejercita el mismo puerto `registrar_lectura` que usará el hardware real.
- (+) Escenarios reproducibles para demostrar alertas.
- (−) HTTP no es óptimo para dispositivos con conectividad limitada; se aborda con MQTT en Inc. 3.

## Atributo de calidad
Capacidad de prueba, interoperabilidad, evolucionabilidad.
