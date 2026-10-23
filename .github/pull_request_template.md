## Historia de usuario

Closes #<!-- n.º del Issue de la HU -->

**HU / RF:** HU-0X / RF-0X — <!-- título -->
**Incremento:** <!-- inc1 | inc2 -->

## Qué cambia

<!-- Resumen breve de los cambios por capa (domain, ports, adapters). -->

## Criterios de aceptación verificados

<!-- Copiar los Dado/Cuando/Entonces de la HU y marcar cada uno. -->
- [ ] CP-RF0X-01:
- [ ] CP-RF0X-02:

## Checklist de la Definition of Done

- [ ] **Pruebas:** unitarias e integración en verde (`pytest -m "not e2e"`); E2E de la HU en verde (`pytest -m e2e`).
- [ ] **Cobertura:** `src/domain` >= 80 % (`--cov-fail-under=80`).
- [ ] **Linter:** `ruff check .` y `ruff format --check .` sin errores.
- [ ] **Pureza del dominio:** `python tools/check_domain_purity.py` reporta M1.1 = 0 % y `lint-imports` en verde.
- [ ] **Captura:** `evidencias/incX/RF0X_paso1_entrada.png` y `RF0X_paso2_resultado.png` generadas por la prueba E2E.
- [ ] **Documentación:** README / ADR / backlog actualizados si aplica; `docs/openapi.json` regenerado (`python tools/export_openapi.py`).
- [ ] **CI:** GitHub Actions en verde.

## Defectos encontrados

<!-- Enlazar Issues con label `bug` abiertos durante esta HU (o "Ninguno"). -->

## Revisión

<!-- GitHub no permite que el autor apruebe su propio PR. Documentar aquí la revisión:
     quién revisó, qué se comprobó y resultado. -->
