# ADR-001: Arquitectura hexagonal (puertos y adaptadores)

- **Estado:** Aceptado
- **Fecha:** 2026-10-23

## Contexto
TruchaSmart debe evolucionar en incrementos (PMV, Inc. 2 y un futuro Inc. 3 con IA y MQTT).
Las reglas del negocio (umbrales, índice de riesgo, FCR, ración) son el activo principal y deben
probarse sin base de datos, sin servidor web y sin sensores reales. La guía de evaluación S9
audita explícitamente la separación dominio / puertos / adaptadores.

## Decisión
Adoptar arquitectura hexagonal con tres capas en `src/`:
- `domain/` (modelo y servicios, incluida la implementación de los casos de uso),
- `ports/` (inbound: casos de uso; outbound: repositorios, notificador, reportes, hash, reloj),
- `adapters/` (REST, web, simulador; persistencia, notificación, reportes, seguridad).

Regla de dependencia `adapters -> ports -> domain`. `domain` y `ports` usan solo la biblioteca
estándar. Se verifica automáticamente con `tools/check_domain_purity.py` (AST) e
`import-linter` en CI.

## Consecuencias
- (+) El dominio se prueba de forma unitaria y rápida; cobertura >= 80 % alcanzable.
- (+) Cambiar PostgreSQL por otro motor, o la API por MQTT, solo afecta adaptadores.
- (−) Más archivos y mapeos (entidad <-> ORM <-> esquema Pydantic).
- (−) Requiere disciplina; mitigada con verificación automática en CI.

## Atributo de calidad
Mantenibilidad (modularidad, capacidad de prueba) y evolucionabilidad.
