# Despliegue · contenedores en ejecución (aplicación y PostgreSQL 16)

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:05 |
| Código de salida | 0 |

```bash
$ docker compose ps && docker images trucha-smart-app
```

```text
NAME                 IMAGE                COMMAND                  SERVICE   CREATED          STATUS                    PORTS
trucha-smart-app-1   trucha-smart-app     "sh -c 'python tools…"   app       36 seconds ago   Up 30 seconds (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
trucha-smart-db-1    postgres:16-alpine   "docker-entrypoint.s…"   db        36 seconds ago   Up 36 seconds (healthy)   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
IMAGE                     ID             DISK USAGE   CONTENT SIZE   EXTRA
trucha-smart-app:latest   e6a34f378ef2        346MB         83.2MB   U    
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
```
