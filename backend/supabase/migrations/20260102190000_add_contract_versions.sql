-- IFRS 16 - Tabela contract_versions (SCD Type 2)
-- Generated: 2026-01-02
-- Esta tabela armazena versões imutáveis dos cálculos IFRS 16 para cada contrato

-- =============================================================================
-- TABELA CONTRACT_VERSIONS
-- =============================================================================

CREATE TABLE IF NOT EXISTS contract_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,

    -- Versionamento
    version_number INTEGER NOT NULL DEFAULT 1,
    version_id VARCHAR(50),  -- Formato: ID{CATEGORIA}{VERSAO}-{NUMERO:04d}

    -- Dados do contrato
    data_inicio DATE NOT NULL,
    prazo_meses INTEGER NOT NULL,
    carencia_meses INTEGER DEFAULT 0,
    parcela_inicial DECIMAL(15, 2) NOT NULL,
    taxa_desconto_anual DECIMAL(8, 4) NOT NULL,

    -- Reajuste
    reajuste_tipo VARCHAR(20) DEFAULT 'nenhum',  -- nenhum, fixo, indice
    reajuste_periodicidade VARCHAR(20) DEFAULT 'anual',  -- mensal, trimestral, semestral, anual
    reajuste_valor DECIMAL(8, 4),  -- Percentual fixo ou null para índice
    mes_reajuste INTEGER,  -- Mês de aplicação do reajuste (1-12)

    -- Resultados dos cálculos (JSON)
    resultados_json TEXT,  -- JSON com todos os detalhes do cálculo

    -- Totais calculados
    total_vp DECIMAL(15, 2),  -- Valor Presente total (Passivo)
    total_nominal DECIMAL(15, 2),  -- Valor Nominal total
    avp DECIMAL(15, 2),  -- Ajuste a Valor Presente

    -- Metadados
    notas TEXT,
    archived_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Índice único para garantir apenas uma versão por número por contrato
CREATE UNIQUE INDEX IF NOT EXISTS uq_contract_version_number
    ON contract_versions (contract_id, version_number);

-- Índice para consultas por contrato
CREATE INDEX IF NOT EXISTS idx_contract_versions_contract_id
    ON contract_versions (contract_id);

-- Índice para consultas por versão mais recente
CREATE INDEX IF NOT EXISTS idx_contract_versions_latest
    ON contract_versions (contract_id, version_number DESC);

-- Índice para relatórios por período
CREATE INDEX IF NOT EXISTS idx_contract_versions_archived
    ON contract_versions (archived_at);

-- Índice para consultas por tipo de reajuste
CREATE INDEX IF NOT EXISTS idx_contract_versions_reajuste
    ON contract_versions (reajuste_tipo, reajuste_periodicidade);

-- Comentário da tabela
COMMENT ON TABLE contract_versions IS 'Versões imutáveis dos cálculos IFRS 16 (SCD Type 2)';
COMMENT ON COLUMN contract_versions.version_id IS 'ID legível: ID{CATEGORIA}{VERSAO}-{NUMERO:04d}';
COMMENT ON COLUMN contract_versions.resultados_json IS 'JSON com cronograma completo de pagamentos e contabilização';
