# Render · HTTP redirige a HTTPS y la cookie de sesión sale con Secure

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:27 |
| Código de salida | 0 |

```bash
$ curl -sS -I http://truchasmart.onrender.com/login && curl -sS -o /dev/null -D - -X POST https://truchasmart.onrender.com/login -d "nombre_usuario=piscicultor&password=Pisci123!" | grep -iE "^HTTP|set-cookie|location"
```

```text
HTTP/1.1 301 Moved Permanently
Date: Fri, 13 Nov 2026 12:35:27 GMT
Content-Type: text/html; charset=utf-8
Connection: keep-alive
Location: https://truchasmart.onrender.com/login
cf-cache-status: DYNAMIC
Server: cloudflare
CF-RAY: a59dd1016efca334-SEA
alt-svc: h3=":443"; ma=86400

HTTP/2 303 
location: /panel
permissions-policy: camera=(), microphone=(), geolocation=()
set-cookie: ts_token=eyJhbGciOiJIUzI1NiIs…(oculto); HttpOnly; Max-Age=28800; Path=/; SameSite=lax; Secure
```
