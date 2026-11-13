# Render · /api/salud del sitio público y cabeceras

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #4 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703 |
| Versión del código | rama `main` @ `f80fe18` |
| Fecha (UTC) | 13/11/2026 04:58:17 |
| Código de salida | 0 |

```bash
$ curl -sS -i --max-time 150 https://truchasmart.onrender.com/api/salud
```

```text
HTTP/2 200 
date: Fri, 13 Nov 2026 04:58:17 GMT
content-type: application/json
cache-control: no-store
content-security-policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'
cross-origin-opener-policy: same-origin
permissions-policy: camera=(), microphone=(), geolocation=()
referrer-policy: strict-origin-when-cross-origin
rndr-id: f365eb4e-cbae-4bfc
server: cloudflare
vary: Accept-Encoding
x-content-type-options: nosniff
x-frame-options: DENY
x-render-origin-server: uvicorn
cf-cache-status: DYNAMIC
cf-ray: a59b33514882f490-ATL
alt-svc: h3=":443"; ma=86400

{"estado":"ok","servicio":"TruchaSmart","base_datos":"ok"}
```
