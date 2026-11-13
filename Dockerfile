FROM python:3.11-slim

WORKDIR /app

# System deps for opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# torch/torchvision solo CPU (la version por defecto en Linux trae CUDA, ~2.5 GB extra)
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.12.1 torchvision==0.27.1 \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Imagenes subidas y base SQLite: montar un volumen persistente en /data
ENV UPLOAD_DIR=/data/uploads
RUN mkdir -p /data/uploads

EXPOSE 8000

# Railway/Render asignan el puerto en $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
