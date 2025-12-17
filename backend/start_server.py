"""
Script para iniciar o servidor com configuração automática
"""
import os
import uvicorn

# Configurar SQLite se não houver DATABASE_URL
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./ifrs16_licenses.db"

# Configurar outras variáveis se não existirem
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "sua-chave-secreta-super-complexa-aqui-mude-isso-em-producao"

if not os.getenv("ADMIN_TOKEN"):
    os.environ["ADMIN_TOKEN"] = "admin-token-super-secreto-mude-isso"

if not os.getenv("ENVIRONMENT"):
    os.environ["ENVIRONMENT"] = "development"

if not os.getenv("DEBUG"):
    os.environ["DEBUG"] = "True"

if not os.getenv("CORS_ORIGINS"):
    os.environ["CORS_ORIGINS"] = "http://localhost,http://127.0.0.1,file://"

print("🚀 Iniciando servidor IFRS 16 License API...")
print("📝 Configuração:")
print(f"   - DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"   - ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
print(f"   - Porta: 8000")
print("\n💡 Acesse:")
print("   - API: http://localhost:8000")
print("   - Docs: http://localhost:8000/docs")
print("   - ReDoc: http://localhost:8000/redoc")
print("\n⚠️  Pressione CTRL+C para parar o servidor\n")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

