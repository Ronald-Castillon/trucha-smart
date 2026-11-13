# Render · pruebas automáticas del despliegue

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:25 |
| Código de salida | 0 |

```bash
$ python -m pytest tests/unit/test_despliegue.py -v -p no:warnings
```

```text
================================================= test session starts ==================================================
platform linux -- Python 3.13.18, pytest-9.2.0, pluggy-1.7.0 -- /opt/hostedtoolcache/Python/3.13.18/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/trucha-smart/trucha-smart
configfile: pyproject.toml
plugins: cov-7.1.0, platformdirs-4.14.5, anyio-4.16.0
collecting ... collected 6 items

tests/unit/test_despliegue.py::test_normaliza_la_url_de_postgresql_del_proveedor[postgres://u:p@host:5432/db-postgresql+psycopg://u:p@host:5432/db] PASSED [ 16%]
tests/unit/test_despliegue.py::test_normaliza_la_url_de_postgresql_del_proveedor[postgresql://u:p@host/db-postgresql+psycopg://u:p@host/db] PASSED [ 33%]
tests/unit/test_despliegue.py::test_normaliza_la_url_de_postgresql_del_proveedor[postgresql+psycopg://u:p@host/db-postgresql+psycopg://u:p@host/db] PASSED [ 50%]
tests/unit/test_despliegue.py::test_normaliza_la_url_de_postgresql_del_proveedor[sqlite:///./truchasmart.db-sqlite:///./truchasmart.db] PASSED [ 66%]
tests/unit/test_despliegue.py::test_si_vacia_crea_la_base_una_vez_y_no_la_vuelve_a_tocar PASSED                  [ 83%]
tests/unit/test_despliegue.py::test_blueprint_de_render_declara_web_docker_y_postgresql PASSED                   [100%]

================================================== 6 passed in 0.07s ===================================================
```
