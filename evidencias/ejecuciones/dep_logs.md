# Despliegue · registro de peticiones del contenedor de la aplicación

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:25 |
| Código de salida | 0 |

```bash
$ docker compose logs app --tail 15
```

```text
app-1  | INFO:     172.18.0.1:58566 - "GET /static/panel.js?v=1794573277 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58566 - "GET /api/estanques HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58566 - "GET /api/alertas?estado=ABIERTA&limite=200 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58566 - "GET /api/panel HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58566 - "GET /api/panel HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "GET /login HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "GET /static/estilos.css?v=1794573277 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "POST /login HTTP/1.1" 303 See Other
app-1  | INFO:     172.18.0.1:58574 - "GET /panel HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "GET /static/vivo.js?v=1794573277 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "GET /static/panel.js?v=1794573277 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "GET /api/estanques HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "GET /api/alertas?estado=ABIERTA&limite=200 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "GET /api/panel HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:58574 - "GET /api/panel HTTP/1.1" 200 OK
```
