# Imagen de la aplicación TruchaSmart (entorno de despliegue de pruebas).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY config ./config
COPY models ./models
COPY db ./db
COPY tools ./tools

# RNF-+ (OWASP A02): el proceso no corre como root
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app

# Puerto: 8000 por defecto; plataformas como Render lo indican en la variable PORT.
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"8000\")}/api/salud')"
# Al arrancar crea el esquema y los datos demo solo si la base está vacía (p. ej. PostgreSQL nuevo).
CMD ["sh", "-c", "python tools/init_db.py --si-vacia && exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
