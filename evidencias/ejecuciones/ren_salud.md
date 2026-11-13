# Render · /api/salud del sitio público y cabeceras

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:27 |
| Código de salida | 0 |

```bash
$ curl -sS -i --max-time 150 https://truchasmart.onrender.com/api/salud
```

```text
HTTP/2 200 
date: Fri, 13 Nov 2026 12:35:27 GMT
content-type: application/json
cache-control: no-store
cf-cache-status: DYNAMIC
content-security-policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'
cross-origin-opener-policy: same-origin
permissions-policy: camera=(), microphone=(), geolocation=()
referrer-policy: strict-origin-when-cross-origin
rndr-id: 7ca00995-683b-4c0b
server: cloudflare
vary: Accept-Encoding
x-content-type-options: nosniff
x-frame-options: DENY
x-render-origin-server: uvicorn
cf-ray: a59dd1009b12e7f7-SEA
alt-svc: h3=":443"; ma=86400

{"estado":"ok","servicio":"TruchaSmart","base_datos":"ok"}
```
