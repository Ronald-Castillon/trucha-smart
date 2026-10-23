# Imagen de la aplicación TruchaSmart (entorno de despliegue de pruebas).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY config ./config
COPY db ./db
COPY tools ./tools

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/salud')"
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
