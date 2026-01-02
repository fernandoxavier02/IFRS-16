-- ============================================
-- DEBUG: Dashboard mostrando valores zerados
-- ============================================

-- 1. Ver TODOS os contratos (sem filtros)
SELECT 
    c.id,
    c.user_id,
    c.name,
    c.status,
    c.is_deleted,
    c.categoria,
    c.created_at
FROM contracts c
ORDER BY c.created_at DESC;

-- 2. Ver contratos COM versões e valores
SELECT 
    c.id as contract_id,
    c.user_id,
    c.name as contract_name,
    c.status,
    c.is_deleted,
    cv.id as version_id,
    cv.version_number,
    cv.total_vp,
    cv.data_inicio,
    cv.prazo_meses
FROM contracts c
LEFT JOIN LATERAL (
    SELECT cv.*
    FROM contract_versions cv
    WHERE cv.contract_id = c.id
    ORDER BY cv.version_number DESC
    LIMIT 1
) cv ON true
ORDER BY c.created_at DESC;

-- 3. Ver usuários cadastrados
SELECT 
    id,
    email,
    created_at
FROM users
ORDER BY created_at DESC;

-- 4. Contar contratos por status
SELECT 
    status,
    is_deleted,
    COUNT(*) as total
FROM contracts
GROUP BY status, is_deleted;

-- 5. Ver contratos do usuário específico (SUBSTITUA o UUID)
-- IMPORTANTE: Pegue o user_id do log do backend que mostra:
-- [DashboardService] Buscando métricas para user_id: XXXXX
SELECT 
    c.id,
    c.name,
    c.status,
    c.is_deleted,
    cv.total_vp
FROM contracts c
LEFT JOIN LATERAL (
    SELECT cv.*
    FROM contract_versions cv
    WHERE cv.contract_id = c.id
    ORDER BY cv.version_number DESC
    LIMIT 1
) cv ON true
WHERE c.user_id = 'COLE_AQUI_O_USER_ID_DO_LOG'::uuid;
