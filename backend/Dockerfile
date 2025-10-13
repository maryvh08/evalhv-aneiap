# backend/Dockerfile
FROM python:3.11-slim

# instalar dependencias del sistema (tesseract, poppler)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    build-essential \
    libxml2-dev libxslt1-dev zlib1g-dev \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Directorio de la app
WORKDIR /app

# Copiar requirements y code
COPY app/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copiar el resto del código
COPY app /app

# Descargar modelo spaCy (ajusta nombre del modelo)
RUN python -m spacy download es_core_news_md

# Crear directorio uploads
RUN mkdir -p /tmp/uploads /tmp/reports

EXPOSE 8000

# Entrypoint
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

