# ADR-003: PostgreSQL en despliegue y SQLite en pruebas, detrás de un puerto

- **Estado:** Aceptado
- **Fecha:** 2026-10-23

## Contexto
B-01 exige registros respaldados. El entorno de pruebas (Windows del equipo y GitHub Actions)
no debe depender de Docker. El despliegue de pruebas sí puede usar docker-compose.

## Decisión
Definir repositorios como puertos de salida (`src/ports/outbound/`) e implementarlos con
SQLAlchemy 2 en `src/adapters/outbound/persistence/`. La URL se toma de `DATABASE_URL`:
PostgreSQL 16 en docker-compose, SQLite (archivo o memoria) en pruebas. El DDL de referencia
está en `db/schema.sql` y los datos demo en `db/seed.sql`.

## Consecuencias
- (+) Pruebas de integración rápidas y reproducibles sin infraestructura.
- (+) Cambiar de motor no toca el dominio.
- (−) Diferencias entre dialectos (zonas horarias, tipos); se usan tipos portables y UTC.

## Atributo de calidad
Portabilidad, fiabilidad (integridad referencial), capacidad de prueba.
