"""
Script para verificar configuração de email SMTP
"""

from app.config import get_settings

settings = get_settings()

print("=" * 60)
print("VERIFICAÇÃO DE CONFIGURAÇÃO DE EMAIL SMTP")
print("=" * 60)
print()

# Verificar cada variável
configs = {
    "SMTP_HOST": settings.SMTP_HOST,
    "SMTP_PORT": settings.SMTP_PORT,
    "SMTP_USER": settings.SMTP_USER,
    "SMTP_PASSWORD": "***" if settings.SMTP_PASSWORD else "",
    "SMTP_FROM_EMAIL": settings.SMTP_FROM_EMAIL,
    "SMTP_FROM_NAME": settings.SMTP_FROM_NAME,
    "SMTP_USE_SSL": settings.SMTP_USE_SSL,
    "SMTP_USE_STARTTLS": settings.SMTP_USE_STARTTLS,
    "SMTP_TIMEOUT_SECONDS": settings.SMTP_TIMEOUT_SECONDS,
}

for key, value in configs.items():
    status = "✅ OK" if value else "❌ MISSING"
    if key == "SMTP_PASSWORD":
        status = "✅ OK" if settings.SMTP_PASSWORD else "❌ MISSING"
    print(f"{key:25} = {str(value):30} {status}")

print()
print("=" * 60)

# Verificar se está configurado
if settings.SMTP_USER and settings.SMTP_PASSWORD:
    print("✅ CONFIGURAÇÃO COMPLETA - Emails podem ser enviados")
else:
    print("⚠️  CONFIGURAÇÃO INCOMPLETA - Emails NÃO serão enviados")
    print()
    print("Variáveis necessárias:")
    print("  - SMTP_USER (obrigatório)")
    print("  - SMTP_PASSWORD (obrigatório)")
    print("  - SMTP_FROM_EMAIL (opcional, usa SMTP_USER se não definido)")
    print()
    print("Adicione essas variáveis ao arquivo .env ou variáveis de ambiente")

print("=" * 60)
