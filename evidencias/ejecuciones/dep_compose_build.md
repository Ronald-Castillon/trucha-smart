# Despliegue · construcción de la imagen y arranque con docker compose

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:34:03 |
| Código de salida | 0 |

```bash
$ docker compose up -d --build --wait 2>&1 | tail -25
```

```text
#17 unpacking to docker.io/library/trucha-smart-app:latest
#17 unpacking to docker.io/library/trucha-smart-app:latest 1.0s done
#17 DONE 5.2s

#18 resolving provenance for metadata file
#18 DONE 0.0s
 Image trucha-smart-app Built 
 Network trucha-smart_default Creating 
 Network trucha-smart_default Created 
 Volume trucha-smart_pgdata Creating 
 Volume trucha-smart_pgdata Created 
 Container trucha-smart-db-1 Creating 
 Container trucha-smart-db-1 Created 
 Container trucha-smart-app-1 Creating 
 Container trucha-smart-app-1 Created 
 Container trucha-smart-db-1 Starting 
 Container trucha-smart-db-1 Started 
 Container trucha-smart-db-1 Waiting 
 Container trucha-smart-db-1 Healthy 
 Container trucha-smart-app-1 Starting 
 Container trucha-smart-app-1 Started 
 Container trucha-smart-app-1 Waiting 
 Container trucha-smart-db-1 Waiting 
 Container trucha-smart-db-1 Healthy 
 Container trucha-smart-app-1 Healthy
```
