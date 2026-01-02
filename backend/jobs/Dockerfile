FROM python:3.11-slim

WORKDIR /app

# Instalar httpx para chamadas HTTP
RUN pip install --no-cache-dir httpx

# Copiar script
COPY sync_economic_indexes.py .

# Executar script
CMD ["python", "sync_economic_indexes.py"]
