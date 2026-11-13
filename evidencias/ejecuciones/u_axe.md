# U · axe-core en las pantallas, móvil a 375 px y teclado

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #4 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703 |
| Versión del código | tag `v3.0-Inc3` @ `fdf2121` |
| Fecha (UTC) | 13/11/2026 04:55:26 |
| Código de salida | 0 |

```bash
$ python -m pytest tests/e2e/test_accesibilidad_axe.py -m e2e -p no:warnings -v
```

```text
================================================= test session starts ==================================================
platform linux -- Python 3.13.18, pytest-9.2.0, pluggy-1.7.0 -- /opt/hostedtoolcache/Python/3.13.18/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/trucha-smart/tag-v3.0-Inc3
configfile: pyproject.toml
plugins: cov-7.1.0, platformdirs-4.14.5, anyio-4.16.0
collecting ... collected 18 items

tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/login] PASSED                      [  5%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/panel] PASSED                      [ 11%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/lecturas/nueva] PASSED             [ 16%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/estanques] PASSED                  [ 22%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/estanques/1] PASSED                [ 27%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/estanques/1/historial?desde=2026-10-16&hasta=2026-10-22] PASSED [ 33%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/lotes/1/produccion] PASSED         [ 38%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/alertas] PASSED                    [ 44%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/reportes] PASSED                   [ 50%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/usuarios] PASSED                   [ 55%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/integraciones] PASSED              [ 61%]
tests/e2e/test_accesibilidad_axe.py::test_pantalla_sin_violaciones_wcag_a_aa[/auditoria] PASSED                  [ 66%]
tests/e2e/test_accesibilidad_axe.py::test_teclado_saltar_al_contenido_y_foco_visible PASSED                      [ 72%]
tests/e2e/test_accesibilidad_axe.py::test_tablas_en_movil_sin_violaciones[/usuarios] PASSED                      [ 77%]
tests/e2e/test_accesibilidad_axe.py::test_tablas_en_movil_sin_violaciones[/alertas] PASSED                       [ 83%]
tests/e2e/test_accesibilidad_axe.py::test_tablas_en_movil_sin_violaciones[/auditoria] PASSED                     [ 88%]
tests/e2e/test_accesibilidad_axe.py::test_tablas_en_movil_sin_violaciones[/estanques] PASSED                     [ 94%]
tests/e2e/test_accesibilidad_axe.py::test_tablas_en_movil_sin_violaciones[/integraciones] PASSED                 [100%]

================================================= 18 passed in 28.88s ==================================================
```
