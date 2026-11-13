# Despliegue · PostgreSQL 16 con los datos cargados

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:06 |
| Código de salida | 0 |

```bash
$ docker compose exec -T db psql -U trucha -d truchasmart -c "SELECT version();" -c "SELECT count(*) AS lecturas FROM lecturas_agua;" -c "SELECT nombre_usuario, rol FROM usuarios ORDER BY id;"
```

```text
                                         version                                          
------------------------------------------------------------------------------------------
 PostgreSQL 16.16 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
(1 row)

 lecturas 
----------
      168
(1 row)

 nombre_usuario |      rol      
----------------+---------------
 admin          | ADMINISTRADOR
 piscicultor    | PISCICULTOR
 operario       | OPERARIO
(3 rows)
```
