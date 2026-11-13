# Despliegue · registro de peticiones del contenedor de la aplicación

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #4 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703 |
| Versión del código | rama `main` @ `f80fe18` |
| Fecha (UTC) | 13/11/2026 04:58:15 |
| Código de salida | 0 |

```bash
$ docker compose logs app --tail 15
```

```text
app-1  | INFO:     172.18.0.1:45812 - "GET /static/panel.js?v=1794545847 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45812 - "GET /api/estanques HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45812 - "GET /api/alertas?estado=ABIERTA&limite=200 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45812 - "GET /api/panel HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45812 - "GET /api/panel HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45828 - "GET /login HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45828 - "GET /static/estilos.css?v=1794545847 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45828 - "POST /login HTTP/1.1" 303 See Other
app-1  | INFO:     172.18.0.1:45828 - "GET /panel HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45828 - "GET /static/vivo.js?v=1794545847 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45836 - "GET /static/panel.js?v=1794545847 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45836 - "GET /api/estanques HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45836 - "GET /api/alertas?estado=ABIERTA&limite=200 HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45836 - "GET /api/panel HTTP/1.1" 200 OK
app-1  | INFO:     172.18.0.1:45836 - "GET /api/panel HTTP/1.1" 200 OK
```
