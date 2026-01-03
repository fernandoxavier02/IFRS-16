"""
Script para verificar se uma licença foi validada
"""
import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import License, ValidationLog, User

async def verificar_licenca(license_key: str):
    """Verifica se uma licença foi validada"""
    
    async with AsyncSessionLocal() as db:
        # Buscar licença
        result = await db.execute(
            select(License).where(License.key == license_key)
        )
        license = result.scalar_one_or_none()
        
        if not license:
            print(f"ERRO: Licenca nao encontrada: {license_key}")
            return
        
        print("=" * 70)
        print(f"INFORMACOES DA LICENCA: {license_key}")
        print("=" * 70)
        print()
        
        # Informações básicas
        print("DADOS DA LICENCA:")
        print(f"   Chave: {license.key}")
        print(f"   Tipo: {license.license_type}")
        print(f"   Status: {license.status}")
        print(f"   Expira em: {license.expires_at}")
        print(f"   Revogada: {'Sim' if license.revoked else 'Não'}")
        print(f"   Máximo de ativações: {license.max_activations}")
        print(f"   Ativações atuais: {license.current_activations}")
        print()
        
        # Verificar se foi validada
        if license.last_validation:
            print("VALIDACAO:")
            print(f"   Última validação: {license.last_validation}")
            print(f"   Machine ID: {license.machine_id or 'Não definido'}")
            print(f"   Total de validações: {license.current_activations}")
            print()
            
            # Buscar logs de validação
            logs_result = await db.execute(
                select(ValidationLog)
                .where(ValidationLog.license_key == license_key)
                .order_by(ValidationLog.timestamp.desc())
            )
            logs = logs_result.scalars().all()
            
            if logs:
                print(f"LOGS DE VALIDACAO ({len(logs)} registro(s)):")
                for i, log in enumerate(logs[:10], 1):  # Mostrar últimos 10
                    status = "SUCESSO" if log.success else "FALHA"
                    print(f"   [{i}] {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {status}")
                    if log.message:
                        print(f"       Mensagem: {log.message}")
                    if log.machine_id:
                        print(f"       Machine: {log.machine_id}")
                    if log.ip_address:
                        print(f"       IP: {log.ip_address}")
                if len(logs) > 10:
                    print(f"   ... e mais {len(logs) - 10} registro(s)")
                print()
            else:
                print("AVISO: Nenhum log de validacao encontrado")
                print()
        else:
            print("VALIDACAO:")
            print("   Licenca NAO foi validada ainda")
            print("   last_validation: NULL")
            print("   machine_id: NULL")
            print("   current_activations: 0")
            print()
            
            # Mesmo sem validação bem-sucedida, verificar se há tentativas
            logs_result = await db.execute(
                select(ValidationLog)
                .where(ValidationLog.license_key == license_key)
                .order_by(ValidationLog.timestamp.desc())
            )
            logs = logs_result.scalars().all()
            
            if logs:
                print(f"TENTATIVAS DE VALIDACAO ({len(logs)} registro(s)):")
                for i, log in enumerate(logs[:10], 1):
                    status = "SUCESSO" if log.success else "FALHA"
                    print(f"   [{i}] {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {status}")
                    if log.message:
                        print(f"       Mensagem: {log.message}")
                    if log.machine_id:
                        print(f"       Machine: {log.machine_id}")
                    if log.ip_address:
                        print(f"       IP: {log.ip_address}")
                if len(logs) > 10:
                    print(f"   ... e mais {len(logs) - 10} registro(s)")
                print()
        
        # Informações do usuário
        if license.user_id:
            user_result = await db.execute(
                select(User).where(User.id == license.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if user:
                print("USUARIO:")
                print(f"   Nome: {user.name}")
                print(f"   Email: {user.email}")
                print(f"   Criado em: {user.created_at}")
                print()
        
        # Resumo
        print("=" * 70)
        if license.last_validation:
            print("STATUS: LICENCA VALIDADA")
            print(f"   Validada {license.current_activations} vez(es)")
            print(f"   Ultima validacao: {license.last_validation.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("STATUS: LICENCA NAO VALIDADA")
            print("   A licenca existe mas ainda nao foi validada")
        print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python verificar_licenca.py <LICENSE_KEY>")
        print("Exemplo: python verificar_licenca.py FX20260103-IFRS16-KUNHCQQW")
        sys.exit(1)
    
    license_key = sys.argv[1].upper().strip()
    asyncio.run(verificar_licenca(license_key))
