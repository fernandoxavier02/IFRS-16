// ============================================================
// FUNÇÕES DE GERENCIAMENTO DE CONTRATOS
// ============================================================

// Carregar contratos ao inicializar
async function loadContracts() {
    // Verificar se CONFIG está definido
    if (typeof CONFIG === 'undefined' || !CONFIG.API_URL) {
        console.warn('CONFIG não está definido ainda, aguardando...');
        setTimeout(loadContracts, 500);
        return;
    }

    // Verificar ambas as chaves para compatibilidade
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) {
        console.log('Nenhum token encontrado, não carregando contratos');
        return;
    }

    // Verificar se os elementos existem
    const container = document.getElementById('contractsList');
    if (!container) {
        console.warn('Elemento contractsList não encontrado ainda');
        return;
    }

    try {
        // Construir URL com filtros
        let url = `${CONFIG.API_URL}/api/contracts?`;
        if (currentFilters.name) url += `search_name=${encodeURIComponent(currentFilters.name)}&`;
        if (currentFilters.code) url += `search_code=${encodeURIComponent(currentFilters.code)}&`;
        if (currentFilters.startDate) url += `start_date=${currentFilters.startDate}&`;
        if (currentFilters.endDate) url += `end_date=${currentFilters.endDate}&`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            contractsData = data.contracts || [];
            renderContracts();
        } else if (response.status === 401) {
            console.log('Token inválido, fazendo logout...');
            if (typeof fazerLogout === 'function') {
                fazerLogout();
            }
        } else if (response.status === 403) {
            // Usuário não tem licença ativa ou não tem permissão
            console.log('Usuário não tem licença ativa para gerenciar contratos');
            const container = document.getElementById('contractsList');
            const countEl = document.getElementById('contractsCount');
            const selectorDiv = document.getElementById('contractSelector');

            if (container) {
                container.innerHTML = `
                    <div class="text-center py-4 text-dark-400">
                        <p class="mb-2">Você precisa de uma licença ativa para gerenciar contratos.</p>
                        <p class="text-xs text-dark-500">Adquira uma licença para começar a usar esta funcionalidade.</p>
                    </div>
                `;
            }
            if (countEl) {
                countEl.textContent = 'Licença necessária';
            }
            if (selectorDiv) {
                selectorDiv.classList.add('hidden');
            }
        } else {
            console.warn('Erro ao carregar contratos:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('Erro ao carregar contratos:', error);
        // Não mostrar erro ao usuário se for apenas um problema de conexão
    }
}

function renderContracts() {
    const container = document.getElementById('contractsList');
    const countEl = document.getElementById('contractsCount');
    const selector = document.getElementById('selectedContract');
    const selectorDiv = document.getElementById('contractSelector');

    // Verificar se os elementos existem
    if (!container || !countEl) {
        console.warn('Elementos de contratos não encontrados');
        return;
    }

    if (contractsData.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-dark-400">
                <p class="mb-3">Você ainda não tem contratos cadastrados.</p>
                <button onclick="openContractModal()" class="btn-primary text-white px-4 py-2 rounded-lg text-sm">
                    Criar Primeiro Contrato
                </button>
            </div>
        `;
        countEl.textContent = 'Nenhum contrato cadastrado';
        selectorDiv.classList.add('hidden');
        return;
    }

    countEl.textContent = `${contractsData.length} contrato(s) cadastrado(s)`;

    if (selectorDiv) {
        selectorDiv.classList.remove('hidden');
    }

    // Limpar e preencher seletor
    if (selector) {
        selector.innerHTML = '<option value="">Selecione um contrato para carregar dados...</option>';
        contractsData.forEach(contract => {
            const option = document.createElement('option');
            option.value = contract.id;
            option.textContent = contract.name;
            if (contract.id === currentContractId) option.selected = true;
            selector.appendChild(option);
        });
    }

    // Renderizar lista
    container.innerHTML = contractsData.map(contract => {
        const statusColors = {
            'draft': 'bg-dark-500/20 text-dark-300 border-dark-500/30',
            'active': 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
            'terminated': 'bg-rose-500/20 text-rose-300 border-rose-500/30'
        };
        const statusLabels = {
            'draft': 'Rascunho',
            'active': 'Ativo',
            'terminated': 'Encerrado'
        };
        const createdDate = new Date(contract.created_at).toLocaleDateString('pt-BR');

        return `
            <div class="bg-dark-900/50 border border-dark-700 rounded-lg p-3 hover:border-primary-500/50 transition-colors">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <h3 class="text-white font-medium text-sm">${contract.name}</h3>
                            <span class="px-2 py-0.5 rounded text-xs border ${statusColors[contract.status]}">
                                ${statusLabels[contract.status]}
                            </span>
                        </div>
                        ${contract.description ? `<p class="text-dark-400 text-xs mb-1">${contract.description}</p>` : ''}
                        ${contract.contract_code ? `<p class="text-dark-500 text-xs">Código: ${contract.contract_code}</p>` : ''}
                        <p class="text-dark-500 text-xs mt-1">Criado em ${createdDate}</p>
                    </div>
                    <div class="flex gap-1 ml-3">
                        <button onclick="openContractDocuments('${contract.id}', '${contract.name.replace(/'/g, "\\'")}')" class="text-cyan-400 hover:text-cyan-300 p-1.5" title="Documentos">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                        </button>
                        <button onclick="verHistoricoVersoes('${contract.id}')" class="text-amber-400 hover:text-amber-300 p-1.5" title="Historico de Versoes">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </button>
                        <button onclick="editContract('${contract.id}')" class="text-primary-400 hover:text-primary-300 p-1.5" title="Editar">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                            </svg>
                        </button>
                        <button onclick="deleteContract('${contract.id}')" class="text-rose-400 hover:text-rose-300 p-1.5" title="Excluir">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function openContractModal(contractId = null) {
    // Verificar ambas as chaves para compatibilidade
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) {
        alert('Você precisa estar logado para gerenciar contratos');
        return;
    }

    const modal = document.getElementById('contractModal');
    const form = document.getElementById('contractForm');
    const title = document.getElementById('modalTitle');

    if (!modal || !form || !title) {
        console.error('Elementos do modal não encontrados');
        return;
    }

    form.reset();
    const contractIdInput = document.getElementById('contractId');
    if (contractIdInput) {
        contractIdInput.value = '';
    }

    if (contractId) {
        const contract = contractsData.find(c => c.id === contractId);
        if (contract) {
            title.textContent = 'Editar Contrato';
            if (contractIdInput) contractIdInput.value = contract.id;
            const nameInput = document.getElementById('contractName');
            const descInput = document.getElementById('contractDescription');
            const codeInput = document.getElementById('contractCode');
            const statusInput = document.getElementById('contractStatus');
            if (nameInput) nameInput.value = contract.name;
            if (descInput) descInput.value = contract.description || '';
            if (codeInput) codeInput.value = contract.contract_code || '';
            if (statusInput) statusInput.value = contract.status;
        }
    } else {
        title.textContent = 'Novo Contrato';
    }

    modal.classList.remove('hidden');
}

function closeContractModal() {
    document.getElementById('contractModal').classList.add('hidden');
}

async function saveContract(event) {
    event.preventDefault();
    // Verificar ambas as chaves para compatibilidade
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) {
        alert('Você precisa estar logado para criar contratos');
        return;
    }

    const contractId = document.getElementById('contractId').value;
    const data = {
        name: document.getElementById('contractName').value,
        description: document.getElementById('contractDescription').value || null,
        contract_code: document.getElementById('contractCode').value || null,
        status: document.getElementById('contractStatus').value
    };

    try {
        const url = contractId
            ? `${CONFIG.API_URL}/api/contracts/${contractId}`
            : `${CONFIG.API_URL}/api/contracts`;
        const method = contractId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeContractModal();
            await loadContracts();
        } else if (response.status === 403) {
            const error = await response.json();
            alert(error.detail || 'Você precisa de uma licença ativa para gerenciar contratos');
        } else {
            const error = await response.json();
            alert(error.detail || 'Erro ao salvar contrato');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão ao salvar contrato');
    }
}

async function editContract(contractId) {
    openContractModal(contractId);
}

async function deleteContract(contractId) {
    if (!confirm('Tem certeza que deseja excluir este contrato?')) {
        return;
    }

    // Verificar ambas as chaves para compatibilidade
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) return;

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/contracts/${contractId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok || response.status === 204) {
            await loadContracts();
        } else {
            const error = await response.json();
            alert(error.detail || 'Erro ao excluir contrato');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão ao excluir contrato');
    }
}

function loadContractData() {
    const selector = document.getElementById('selectedContract');
    if (!selector) return;

    const contractId = selector.value;
    if (!contractId) {
        currentContractId = null;
        // Esconder botões
        const btnProcessar = document.getElementById('btnProcessarContrato');
        const btnArquivar = document.getElementById('btnArquivarVersao');
        if (btnProcessar) btnProcessar.classList.add('hidden');
        if (btnArquivar) btnArquivar.classList.add('hidden');
        return;
    }
    currentContractId = contractId;
    console.log('Contrato selecionado:', contractId);
}

function toggleFilters() {
    const panel = document.getElementById('filtersPanel');
    if (panel) {
        panel.classList.toggle('hidden');
    }
}

async function applyFilters() {
    currentFilters = {
        name: document.getElementById('filterName')?.value || '',
        code: document.getElementById('filterCode')?.value || '',
        startDate: document.getElementById('filterStartDate')?.value || '',
        endDate: document.getElementById('filterEndDate')?.value || ''
    };
    await loadContracts();
}

function clearFilters() {
    const filterName = document.getElementById('filterName');
    const filterCode = document.getElementById('filterCode');
    const filterStartDate = document.getElementById('filterStartDate');
    const filterEndDate = document.getElementById('filterEndDate');

    if (filterName) filterName.value = '';
    if (filterCode) filterCode.value = '';
    if (filterStartDate) filterStartDate.value = '';
    if (filterEndDate) filterEndDate.value = '';

    currentFilters = { name: '', code: '', startDate: '', endDate: '' };
    loadContracts();
}

async function loadEconomicIndexes() {
    // Verificar ambas as chaves para compatibilidade
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) return;

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/economic-indexes?limit=1000`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            economicIndexes = {};
            data.indexes.forEach(idx => {
                if (!economicIndexes[idx.index_type]) {
                    economicIndexes[idx.index_type] = [];
                }
                economicIndexes[idx.index_type].push(idx);
            });
            console.log('Índices econômicos carregados:', economicIndexes);
        } else if (response.status === 404) {
            // API de índices ainda não implementada - usar modo manual
            console.log('API de índices econômicos não disponível - usando modo manual');
            economicIndexes = {};
        }
    } catch (error) {
        console.error('Erro ao carregar índices:', error);
    }
}

async function handleReajusteChange() {
    const tipo = document.getElementById('reajusteTipo')?.value;
    const container = document.getElementById('reajusteManualContainer');
    const input = document.getElementById('reajusteAnual');
    const info = document.getElementById('reajusteIndicadorInfo');

    if (!tipo || !container || !input) return;

    if (tipo === 'manual') {
        input.disabled = false;
        if (info) info.textContent = '';
    } else {
        const indexes = economicIndexes[tipo];
        if (indexes && indexes.length > 0) {
            const latest = indexes.sort((a, b) =>
                new Date(b.reference_date) - new Date(a.reference_date)
            )[0];

            input.value = parseFloat(latest.value).toFixed(2);
            input.disabled = true;

            if (info) {
                const refDate = new Date(latest.reference_date);
                info.textContent = `(Último: ${refDate.toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })} - ${parseFloat(latest.value).toFixed(2)}%)`;
            }
        } else {
            input.disabled = false;
            if (info) info.textContent = '(Índice não disponível - use manual)';
        }
    }

    calcular();
}

async function arquivarVersao() {
    if (!currentContractId) {
        alert('Por favor, selecione um contrato antes de arquivar uma versão.');
        return;
    }

    if (!dadosCalculados || !dadosCalculados.inputs) {
        alert('Por favor, calcule o contrato antes de arquivar uma versão.');
        return;
    }

    const notas = prompt('Adicione observações para esta versão (opcional):');
    if (notas === null) return;

    // Verificar ambas as chaves para compatibilidade
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) {
        alert('Você precisa estar logado para arquivar versões');
        return;
    }

    try {
        const reajusteTipo = document.getElementById('reajusteTipo')?.value || 'manual';
        const reajusteValor = reajusteTipo === 'manual' ? parseFloat(document.getElementById('reajusteAnual').value) : null;

        const versionData = {
            data_inicio: dadosCalculados.inputs.dataInicio.toISOString().split('T')[0],
            prazo_meses: dadosCalculados.inputs.prazoMeses,
            carencia_meses: dadosCalculados.inputs.carenciaMeses,
            parcela_inicial: dadosCalculados.inputs.parcelaInicial,
            taxa_desconto_anual: dadosCalculados.inputs.taxaAnual,
            reajuste_tipo: reajusteTipo,
            reajuste_valor: reajusteValor,
            mes_reajuste: parseInt(document.getElementById('mesReajuste').value),
            resultados_json: {
                fluxoCaixa: dadosCalculados.fluxoCaixa,
                contabilizacao: dadosCalculados.contabilizacao,
                cpLp: dadosCalculados.cpLp
            },
            total_vp: dadosCalculados.totalVP,
            total_nominal: dadosCalculados.totalNominal,
            avp: dadosCalculados.avp,
            notas: notas || null
        };

        const response = await fetch(`${CONFIG.API_URL}/api/contracts/${currentContractId}/versions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(versionData)
        });

        if (response.ok) {
            const version = await response.json();
            alert(`Versão ${version.version_number} arquivada com sucesso!`);
        } else {
            const error = await response.json();
            alert(`Erro ao arquivar versão: ${error.detail || 'Erro desconhecido'}`);
        }
    } catch (error) {
        console.error('Erro ao arquivar versão:', error);
        alert('Erro ao arquivar versão. Verifique o console para mais detalhes.');
    }
}

async function processarContrato() {
    if (!currentContractId) {
        alert('Por favor, selecione um contrato antes de processar.');
        return;
    }

    if (!dadosCalculados || !dadosCalculados.inputs) {
        alert('Por favor, calcule o contrato antes de processar.');
        return;
    }

    // Verificar ambas as chaves para compatibilidade
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) {
        alert('Você precisa estar logado para processar contratos');
        return;
    }

    // Pedir observações opcionais
    const notas = prompt('Adicione observações para esta versão (opcional):\n\nDeixe em branco para salvar sem observações.');
    if (notas === null) return; // Usuário cancelou

    try {
        const reajusteTipo = document.getElementById('reajusteTipo')?.value || 'manual';
        const reajusteValor = reajusteTipo === 'manual' ? parseFloat(document.getElementById('reajusteAnual').value) : null;

        const versionData = {
            data_inicio: dadosCalculados.inputs.dataInicio.toISOString().split('T')[0],
            prazo_meses: dadosCalculados.inputs.prazoMeses,
            carencia_meses: dadosCalculados.inputs.carenciaMeses,
            parcela_inicial: dadosCalculados.inputs.parcelaInicial,
            taxa_desconto_anual: dadosCalculados.inputs.taxaAnual,
            reajuste_tipo: reajusteTipo,
            reajuste_valor: reajusteValor,
            mes_reajuste: parseInt(document.getElementById('mesReajuste').value),
            resultados_json: {
                fluxoCaixa: dadosCalculados.fluxoCaixa,
                contabilizacao: dadosCalculados.contabilizacao,
                cpLp: dadosCalculados.cpLp
            },
            total_vp: dadosCalculados.totalVP,
            total_nominal: dadosCalculados.totalNominal,
            avp: dadosCalculados.avp,
            notas: notas || null
        };

        const response = await fetch(`${CONFIG.API_URL}/api/contracts/${currentContractId}/versions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(versionData)
        });

        if (response.ok) {
            const version = await response.json();
            alert(`✅ Contrato processado com sucesso!\n\nVersão ${version.version_number} gravada.`);
        } else {
            const errorText = await response.text();
            let errorMessage = 'Erro ao processar contrato';
            try {
                const error = JSON.parse(errorText);
                errorMessage = error.detail || error.message || errorMessage;
            } catch (e) {
                errorMessage = errorText || errorMessage;
            }
            alert(`❌ Erro ao processar contrato:\n${errorMessage}`);
            console.error('Erro completo:', response.status, errorText);
        }
    } catch (error) {
        console.error('Erro ao processar contrato:', error);
        alert('❌ Erro ao processar contrato. Verifique o console para mais detalhes.');
    }
}

async function verHistoricoVersoes(contractId) {
    // Verificar ambas as chaves para compatibilidade
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) {
        alert('Você precisa estar logado');
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/contracts/${contractId}/versions`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Dados recebidos:', data);

            // Verificar estrutura da resposta
            const versions = data.versions || (Array.isArray(data) ? data : []);

            if (versions.length > 0) {
                let html = '<div class="space-y-2">';
                versions.forEach(v => {
                    const date = new Date(v.archived_at || v.created_at).toLocaleString('pt-BR');
                    html += `
                        <div class="glass-card-light p-3 rounded-lg">
                            <div class="flex justify-between items-start">
                                <div>
                                    <p class="font-semibold text-white">Versão ${v.version_number}</p>
                                    <p class="text-xs text-dark-400">${date}</p>
                                    ${v.notas ? `<p class="text-sm text-dark-300 mt-1">${v.notas}</p>` : ''}
                                </div>
                                <div class="text-right">
                                    <p class="text-sm text-primary-400">VP: R$ ${parseFloat(v.total_vp || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                                    <p class="text-xs text-dark-400">${v.prazo_meses} meses</p>
                                </div>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';

                const modal = document.createElement('div');
                modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4';
                modal.innerHTML = `
                    <div class="glass-card rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-semibold text-white">Histórico de Versões</h3>
                            <button onclick="this.closest('.fixed').remove()" class="text-dark-400 hover:text-white">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>
                        ${html}
                    </div>
                `;
                document.body.appendChild(modal);
            } else {
                alert('Nenhuma versão arquivada para este contrato.');
            }
        } else {
            const errorText = await response.text();
            let errorMessage = 'Erro ao carregar histórico de versões';
            try {
                const error = JSON.parse(errorText);
                errorMessage = error.detail || error.message || errorMessage;
            } catch (e) {
                errorMessage = errorText || errorMessage;
            }
            console.error('Erro ao carregar versões:', response.status, errorMessage);
            alert(`❌ Erro ao carregar histórico:\n${errorMessage}\n\nStatus: ${response.status}`);
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
        alert(`❌ Erro ao carregar histórico:\n${error.message || 'Erro desconhecido'}`);
    }
}

// ============================================================
// FUNÇÃO PARA GRAVAR CONTRATO COM VERSÃO
// ============================================================

async function gravarContratoComVersao() {
    // Verificar token
    const token = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    if (!token) {
        alert('❌ Você precisa estar logado para gravar contratos.\n\nFaça login primeiro.');
        return;
    }

    // Verificar se há dados calculados
    if (typeof dadosCalculados === 'undefined' || !dadosCalculados || !dadosCalculados.inputs) {
        alert('❌ Por favor, preencha os dados do contrato e aguarde o cálculo antes de gravar.');
        return;
    }

    // Pedir nome do contrato
    const nomeContrato = prompt('📝 Digite o nome do contrato:\n\n(Ex: Aluguel Sede SP, Veículo Frota 01, etc.)');
    if (!nomeContrato || nomeContrato.trim() === '') {
        alert('❌ Nome do contrato é obrigatório.');
        return;
    }

    // Pedir código opcional
    const codigoContrato = prompt('🔢 Digite o código do contrato (opcional):\n\n(Ex: CONT-2025-001, deixe em branco para pular)') || null;

    // Pedir observações opcionais
    const notas = prompt('📋 Adicione observações para esta versão (opcional):\n\nDeixe em branco para salvar sem observações.') || null;

    try {
        // 1. Criar o contrato primeiro
        const contractResponse = await fetch(`${CONFIG.API_URL}/api/contracts`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: nomeContrato.trim(),
                description: notas,
                contract_code: codigoContrato,
                status: 'active'
            })
        });

        if (!contractResponse.ok) {
            const error = await contractResponse.json();
            if (contractResponse.status === 403) {
                alert('❌ Você precisa de uma licença ativa para criar contratos.\n\nAdquira uma licença para usar esta funcionalidade.');
            } else {
                alert(`❌ Erro ao criar contrato:\n${error.detail || 'Erro desconhecido'}`);
            }
            return;
        }

        const contract = await contractResponse.json();
        console.log('Contrato criado:', contract);

        // 2. Criar a versão do contrato
        const reajusteTipo = document.getElementById('reajusteTipo')?.value || 'manual';
        const reajusteValor = reajusteTipo === 'manual' ? parseFloat(document.getElementById('reajusteAnual')?.value || 5) : null;

        const versionData = {
            data_inicio: dadosCalculados.inputs.dataInicio.toISOString().split('T')[0],
            prazo_meses: dadosCalculados.inputs.prazoMeses,
            carencia_meses: dadosCalculados.inputs.carenciaMeses,
            parcela_inicial: dadosCalculados.inputs.parcelaInicial,
            taxa_desconto_anual: dadosCalculados.inputs.taxaAnual,
            reajuste_tipo: reajusteTipo,
            reajuste_valor: reajusteValor,
            mes_reajuste: parseInt(document.getElementById('mesReajuste')?.value || 1),
            resultados_json: {
                fluxoCaixa: dadosCalculados.fluxoCaixa,
                contabilizacao: dadosCalculados.contabilizacao,
                cpLp: dadosCalculados.cpLp
            },
            total_vp: dadosCalculados.totalVP,
            total_nominal: dadosCalculados.totalNominal,
            avp: dadosCalculados.avp,
            notas: notas
        };

        const versionResponse = await fetch(`${CONFIG.API_URL}/api/contracts/${contract.id}/versions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(versionData)
        });

        if (!versionResponse.ok) {
            const error = await versionResponse.json();
            alert(`❌ Contrato criado, mas erro ao salvar versão:\n${error.detail || 'Erro desconhecido'}`);
            return;
        }

        const version = await versionResponse.json();
        console.log('Versão criada:', version);

        // 3. Atualizar lista de contratos
        await loadContracts();

        // 4. Selecionar o contrato recém-criado
        currentContractId = contract.id;
        const selector = document.getElementById('selectedContract');
        if (selector) {
            selector.value = contract.id;
        }

        // Mostrar botões de processar/arquivar
        const btnProcessar = document.getElementById('btnProcessarContrato');
        const btnArquivar = document.getElementById('btnArquivarVersao');
        if (btnProcessar) btnProcessar.classList.remove('hidden');
        if (btnArquivar) btnArquivar.classList.remove('hidden');

        alert(`✅ Contrato gravado com sucesso!\n\n📄 Nome: ${nomeContrato}\n📊 Versão: ${version.version_number}\n💰 VP: R$ ${dadosCalculados.totalVP.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`);

    } catch (error) {
        console.error('Erro ao gravar contrato:', error);
        alert(`❌ Erro ao gravar contrato:\n${error.message || 'Erro desconhecido'}`);
    }
}

// ============================================================
// FUNCAO PARA ABRIR MODAL DE DOCUMENTOS
// ============================================================

function openContractDocuments(contractId, contractName) {
    // Verificar se DocumentManager esta disponivel
    if (typeof DocumentManager === 'undefined') {
        console.error('DocumentManager nao carregado');
        alert('Erro: Modulo de documentos nao carregado. Recarregue a pagina.');
        return;
    }

    DocumentManager.openContractDocumentsModal(contractId, contractName);
}

// Expor funcao globalmente para uso em onclick inline
window.openContractDocuments = openContractDocuments;
