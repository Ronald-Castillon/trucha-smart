# Historial de mediciones de confiabilidad y rendimiento

Salidas literales de `tools/prueba_confiabilidad.py` y `tools/prueba_carga.py` en ejecuciones
locales (Windows 11, 20 núcleos). El resultado vigente de cada prueba está en `docs/calidad/`.

| Archivo | Prueba | Base de datos | Fecha |
|---|---|---|---|
| `rendimiento_2_wal_pool_4workers.*` | Carga, 500 usuarios, 4 workers (corrección del defecto #39) | SQLite WAL | 30/10/2026 |
| `rendimiento_3_wal_pool_8workers.*` | Carga, 500 usuarios, 8 workers | SQLite WAL | 30/10/2026 |
| `s12_confiabilidad_sqlite.*` | Caos: 3 caídas del proceso en 90 s | SQLite | 06/11/2026 |
| `s12_rendimiento_sqlite.*` | Carga, 500 usuarios, 8 workers | SQLite | 06/11/2026 |
| `s12_confiabilidad_postgresql_docker.*` | Caos con la base detenida ~10 s | PostgreSQL 16 en Docker | 06/11/2026 |
| `s12_rendimiento_postgresql_docker.*` | Carga, 500 usuarios, 4 workers (no cumple p95, Issue #42) | PostgreSQL 16 en Docker | 06/11/2026 |
