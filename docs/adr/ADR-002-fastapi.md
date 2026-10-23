# ADR-002: FastAPI como framework del adaptador REST/web

- **Estado:** Aceptado
- **Fecha:** 2026-10-23

## Contexto
Se requiere una API JSON para el simulador y clientes futuros, una interfaz web responsiva sin
Node y un contrato documentado (OpenAPI) verificable en CI. El equipo domina Python.

## Decisión
Usar FastAPI + Uvicorn para los adaptadores de entrada `rest/` y `web/` (Jinja2 + Chart.js por CDN).
Pydantic se usa solo en esquemas del adaptador REST. El contrato se exporta a `docs/openapi.json`
y CI falla si no coincide con el código (`tools/export_openapi.py --check`).

## Consecuencias
- (+) OpenAPI generado automáticamente; validación de entrada declarativa.
- (+) `TestClient` permite pruebas de integración sin levantar servidor.
- (−) Pydantic podría "filtrarse" al dominio; se previene con import-linter.

## Atributo de calidad
Interoperabilidad, productividad del desarrollo, capacidad de prueba.
