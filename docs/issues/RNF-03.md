---
titulo: "RNF-+: Seguridad de código (OWASP 2025) y restricciones técnicas"
labels: rnf,inc3
milestone: Incremento 3
---
**FURPS+:** + (seguridad y restricciones) · **Rama:** `rnf/seguridad-sast`

### Criterios de aceptación
- Análisis SAST con **Bandit** sobre `src/`: 0 hallazgos de severidad alta o media.
- Auditoría de dependencias con **pip-audit**: 0 vulnerabilidades conocidas.
- Cabeceras de seguridad HTTP (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
- La app no arranca en producción con la clave JWT por defecto.
- Dependabot configurado; CI construye la imagen Docker (restricción de despliegue).
- Matriz OWASP Top 10 2025 con la mitigación implementada y su evidencia en el repositorio.
