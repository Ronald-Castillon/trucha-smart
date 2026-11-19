## DESCRIPCIÓN DEL CAMBIO

- **Resumen:** [Breve explicación de las modificaciones de código]
- **Fixes Issue:** Closes #<!-- n.º del Issue de la Solicitud de Cambio o de la HU -->
- **Rama de origen → destino (GitFlow):** <!-- feature/* → develop · release/* → main · hotfix/* → main -->
- **Versión de destino (SemVer):** <!-- p. ej. v4.1.0 -->

## CHECKLIST DE CRITERIOS DE TERMINACIÓN (Definition of Done)

- [ ] Código compilado sin errores (la imagen Docker se construye en CI).
- [ ] Pruebas unitarias aprobadas con cobertura >= 80% (`pytest -m "not e2e" --cov=src/domain --cov-fail-under=80`).
- [ ] Estructura conforme a Arquitectura Hexagonal (/src/domain/ desacoplado: `tools/check_domain_purity.py` y `lint-imports` en verde).
- [ ] Linter sin errores (`ruff check .` y `ruff format --check .`).
- [ ] Pruebas E2E de la HU en verde y capturas en `evidencias/` (si cambia la interfaz).
- [ ] Documentación actualizada (README, ADR, `docs/openapi.json`) si aplica.

## REVISIÓN DE CÓDIGO (Code Review)

<!-- Un par distinto del autor revisa «Files changed» y aprueba con «Review changes → Approve».
     La protección de ramas de main y develop exige 1 aprobación y los checks de CI. -->
- **Revisor:** @
- **Qué se comprobó:**
