FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta (Cloud Run usa PORT)
ENV PORT=8080
EXPOSE 8080

# Comando de start
# Cloud Run fornece PORT via variável de ambiente
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
