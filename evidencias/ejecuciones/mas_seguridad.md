# + · Pruebas de cabeceras, auditoría y configuración segura

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | tag `v3.0-Inc3` @ `fdf2121` |
| Fecha (UTC) | 13/11/2026 12:33:56 |
| Código de salida | 0 |

```bash
$ python -m pytest tests/integration/test_seguridad_http.py tests/integration/test_api_auditoria.py tests/unit/test_seguridad.py -p no:warnings -v
```

```text
================================================= test session starts ==================================================
platform linux -- Python 3.13.18, pytest-9.2.0, pluggy-1.7.0 -- /opt/hostedtoolcache/Python/3.13.18/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/trucha-smart/tag-v3.0-Inc3
configfile: pyproject.toml
plugins: cov-7.1.0, platformdirs-4.14.5, anyio-4.16.0
collecting ... collected 8 items

tests/integration/test_seguridad_http.py::test_cabeceras_de_seguridad_en_web_y_api PASSED                        [ 12%]
tests/integration/test_seguridad_http.py::test_produccion_rechaza_la_clave_jwt_de_ejemplo_o_corta PASSED         [ 25%]
tests/integration/test_api_auditoria.py::test_cp_rf11_01_api_responde_423_y_desbloquea_a_los_5_minutos PASSED    [ 37%]
tests/integration/test_api_auditoria.py::test_login_web_muestra_el_bloqueo PASSED                                [ 50%]
tests/integration/test_api_auditoria.py::test_cp_rf11_02_bitacora_registra_accesos_y_claves PASSED               [ 62%]
tests/unit/test_seguridad.py::test_cp_rf11_01_tres_fallos_bloquean_cinco_minutos PASSED                          [ 75%]
tests/unit/test_seguridad.py::test_un_acierto_reinicia_el_contador PASSED                                        [ 87%]
tests/unit/test_seguridad.py::test_cp_rf11_02_bitacora_sin_secretos_y_solo_para_admin PASSED                     [100%]

================================================== 8 passed in 0.80s ===================================================
```
