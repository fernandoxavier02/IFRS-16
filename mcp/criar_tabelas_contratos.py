"""
Script para criar tabelas de contratos e versões no Cloud SQL
"""
import asyncio
import asyncpg

async def create_tables():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    print("Conectado ao banco de dados...")
    
    # Criar tabela de contratos (ou adicionar colunas faltantes)
    print("Criando/atualizando tabela contracts...")
    
    # Verificar se tabela existe
    table_exists = await conn.fetchval('''
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'contracts'
        )
    ''')
    
    if not table_exists:
        await conn.execute('''
            CREATE TABLE contracts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                contract_code VARCHAR(100),
                status VARCHAR(50) DEFAULT 'draft',
                is_deleted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP,
                deleted_at TIMESTAMP
            )
        ''')
    else:
        # Garantir que todas as colunas existem
        await conn.execute('ALTER TABLE contracts ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE')
        await conn.execute('ALTER TABLE contracts ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP')
        await conn.execute('ALTER TABLE contracts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP')
    print("✅ Tabela contracts criada!")
    
    # Criar índices para contracts
    await conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_contracts_user_id ON contracts(user_id)
    ''')
    await conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)
    ''')
    print("✅ Índices de contracts criados!")
    
    # Criar tabela de versões de contratos (imutáveis)
    print("Criando tabela contract_versions...")
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS contract_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
            version_number INTEGER NOT NULL,
            
            -- Dados do contrato
            data_inicio DATE NOT NULL,
            prazo_meses INTEGER NOT NULL,
            carencia_meses INTEGER DEFAULT 0,
            parcela_inicial DECIMAL(18, 2) NOT NULL,
            taxa_desconto_anual DECIMAL(10, 6) NOT NULL,
            
            -- Reajuste
            reajuste_tipo VARCHAR(50) DEFAULT 'manual',
            reajuste_valor DECIMAL(10, 4),
            mes_reajuste INTEGER DEFAULT 1,
            
            -- Resultados calculados (JSON imutável)
            resultados_json JSONB NOT NULL,
            
            -- Totais
            total_vp DECIMAL(18, 2) NOT NULL,
            total_nominal DECIMAL(18, 2) NOT NULL,
            avp DECIMAL(18, 2) NOT NULL,
            
            -- Metadados
            notas TEXT,
            archived_at TIMESTAMP DEFAULT NOW(),
            created_at TIMESTAMP DEFAULT NOW(),
            
            -- Constraint de unicidade para versão por contrato
            UNIQUE(contract_id, version_number)
        )
    ''')
    print("✅ Tabela contract_versions criada!")
    
    # Criar índices para contract_versions
    await conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_contract_versions_contract_id ON contract_versions(contract_id)
    ''')
    await conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_contract_versions_archived_at ON contract_versions(archived_at)
    ''')
    print("✅ Índices de contract_versions criados!")
    
    # Verificar tabelas criadas
    tables = await conn.fetch('''
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('contracts', 'contract_versions')
    ''')
    
    print("\n" + "="*50)
    print("TABELAS CRIADAS:")
    print("="*50)
    for t in tables:
        print(f"  ✅ {t['table_name']}")
    
    await conn.close()
    print("\n✅ Script concluído com sucesso!")

if __name__ == "__main__":
    asyncio.run(create_tables())
