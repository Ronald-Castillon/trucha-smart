"""Cabeceras de seguridad HTTP (RNF-+, OWASP A02 Security Misconfiguration).

La CSP permite scripts propios, Chart.js desde cdn.jsdelivr.net y los scripts en línea de las
plantillas ('unsafe-inline': deuda registrada en docs/calidad/seguridad_owasp_2025.md).
Swagger UI (/docs) y ReDoc (/redoc) cargan recursos de CDN y quedan sin CSP.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ]
)
CABECERAS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}
SIN_CSP = ("/docs", "/redoc")


class CabecerasSeguridad(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        respuesta = await call_next(request)
        for nombre, valor in CABECERAS.items():
            respuesta.headers.setdefault(nombre, valor)
        if not request.url.path.startswith(SIN_CSP):
            respuesta.headers.setdefault("Content-Security-Policy", CSP)
        if request.url.path.startswith("/api/"):
            respuesta.headers.setdefault("Cache-Control", "no-store")
        return respuesta
