FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema (raramente muda - fica em cache)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar APENAS requirements primeiro (cache de pip)
COPY requirements.txt .

# Usar cache do pip para acelerar builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copiar código (isso invalida cache só quando código muda)
COPY . .

# Expor porta (Cloud Run usa PORT)
ENV PORT=8080
EXPOSE 8080

# Comando de start
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
