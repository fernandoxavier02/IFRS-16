#!/bin/bash
# Script de build para Render

set -e  # Parar em caso de erro

echo "🔨 Instalando dependências Python..."
pip install -r requirements.txt

echo "📦 Executando migrações do banco de dados..."
cd backend || exit 1
alembic upgrade head

echo "✅ Build concluído com sucesso!"

