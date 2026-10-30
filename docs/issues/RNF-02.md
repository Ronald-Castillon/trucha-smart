---
titulo: "RNF-R/P: Pruebas de confiabilidad y de rendimiento"
labels: rnf,inc3
milestone: Incremento 3
---
**FURPS+:** R (Reliability) y P (Performance) · **Rama:** `rnf/confiabilidad-rendimiento`

### Criterios de aceptación
- `/api/salud` verifica la base de datos y responde 503 si no está disponible (sin caerse).
- **Confiabilidad:** prueba de caos que mata el proceso del servidor varias veces bajo un supervisor y mide disponibilidad (%), MTTR y MTBF; prueba de caída de PostgreSQL que mide el tiempo de reconexión automática. Umbrales de la guía: disponibilidad ≥ 99.5 %, MTTR < 5 min.
- **Rendimiento:** prueba de carga con Locust (equivalente a k6) sobre los endpoints principales que mide latencia p95, throughput (RPS) y memoria del servidor. Umbral de la guía: p95 < 800 ms con 500 usuarios.
- Los resultados se guardan en `docs/calidad/` y CI los ejecuta contra PostgreSQL.
