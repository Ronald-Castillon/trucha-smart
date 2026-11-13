# R · /api/salud responde 503 sin caerse cuando falla la base de datos

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #4 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703 |
| Versión del código | tag `v3.0-Inc3` @ `fdf2121` |
| Fecha (UTC) | 13/11/2026 04:55:24 |
| Código de salida | 0 |

```bash
$ python -m pytest tests/integration/test_salud.py -p no:warnings -v
```

```text
================================================= test session starts ==================================================
platform linux -- Python 3.13.18, pytest-9.2.0, pluggy-1.7.0 -- /opt/hostedtoolcache/Python/3.13.18/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/trucha-smart/tag-v3.0-Inc3
configfile: pyproject.toml
plugins: cov-7.1.0, platformdirs-4.14.5, anyio-4.16.0
collecting ... collected 3 items

tests/integration/test_salud.py::test_salud_responde_ok PASSED                                                   [ 33%]
tests/integration/test_salud.py::test_salud_responde_503_sin_caerse_si_la_bd_no_esta PASSED                      [ 66%]
tests/integration/test_salud.py::test_openapi_exportado_esta_actualizado PASSED                                  [100%]

================================================== 3 passed in 0.39s ===================================================
```
