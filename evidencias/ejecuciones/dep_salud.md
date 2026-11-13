# Despliegue · /api/salud y cabeceras de seguridad

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:06 |
| Código de salida | 0 |

```bash
$ curl -s http://localhost:8000/api/salud && echo && curl -s -D - -o /dev/null http://localhost:8000/login
```

```text
{"estado":"ok","servicio":"TruchaSmart","base_datos":"ok"}
HTTP/1.1 200 OK
date: Fri, 13 Nov 2026 12:35:05 GMT
server: uvicorn
content-length: 931
content-type: text/html; charset=utf-8
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
permissions-policy: camera=(), microphone=(), geolocation=()
cross-origin-opener-policy: same-origin
content-security-policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'
```
