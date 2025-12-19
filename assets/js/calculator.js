// ============================================================
// FUNÇÕES DE CÁLCULO FINANCEIRO E CONTÁBIL
// ============================================================

function calcular() {
    const inputs = {
        dataInicio: new Date(document.getElementById('dataInicio').value + 'T00:00:00'),
        prazoMeses: parseInt(document.getElementById('prazoMeses').value) || 60,
        carenciaMeses: parseInt(document.getElementById('carenciaMeses').value) || 0,
        taxaAnual: parseFloat(document.getElementById('taxaAnual').value) || 0,
        reajusteAnual: parseFloat(document.getElementById('reajusteAnual').value) || 0,
        mesReajuste: parseInt(document.getElementById('mesReajuste').value) || 1,
        parcelaInicial: parseFloat(document.getElementById('parcelaInicial').value) || 0
    };

    const taxaMensal = Math.pow(1 + inputs.taxaAnual / 100, 1 / 12) - 1;
    const anoInicio = inputs.dataInicio.getFullYear();
    document.getElementById('taxaMensal').textContent = formatPercent(taxaMensal * 100, 4);

    const fluxoCaixa = [];
    let totalNominal = 0, totalVP = 0;

    for (let mes = 1; mes <= inputs.prazoMeses; mes++) {
        const dataAtual = new Date(inputs.dataInicio);
        dataAtual.setMonth(dataAtual.getMonth() + mes - 1);
        const anoAtual = dataAtual.getFullYear();
        const mesAtual = dataAtual.getMonth() + 1;
        let parcela = 0;
        if (mes > inputs.carenciaMeses) {
            let reajustes = 0;
            for (let ano = anoInicio + 1; ano <= anoAtual; ano++) {
                if (ano < anoAtual || (ano === anoAtual && mesAtual >= inputs.mesReajuste)) reajustes++;
            }
            parcela = inputs.parcelaInicial * Math.pow(1 + inputs.reajusteAnual / 100, reajustes);
        }
        const fatorDesconto = 1 / Math.pow(1 + taxaMensal, mes);
        const valorPresente = parcela * fatorDesconto;
        totalNominal += parcela;
        totalVP += valorPresente;
        fluxoCaixa.push({ mes, data: formatDataMes(dataAtual), dataObj: new Date(dataAtual), parcela, fatorDesconto, valorPresente });
    }

    const contabilizacao = [];
    let passivoAtual = totalVP, deprecAcumulada = 0;
    const deprecMensal = totalVP / inputs.prazoMeses;
    contabilizacao.push({ mes: 0, data: formatDataMes(inputs.dataInicio), passivoInicial: 0, juros: 0, pagamento: 0, passivoFinal: totalVP, ativoBruto: totalVP, deprecAcum: 0, ativoLiquido: totalVP, despJuros: 0, despDeprec: 0, despTotal: 0 });

    for (let mes = 1; mes <= inputs.prazoMeses; mes++) {
        const passivoInicial = passivoAtual;
        const juros = passivoInicial * taxaMensal;
        const pagamento = fluxoCaixa[mes - 1].parcela;
        const passivoFinal = passivoInicial + juros - pagamento;
        deprecAcumulada += deprecMensal;
        contabilizacao.push({ mes, data: fluxoCaixa[mes - 1].data, passivoInicial, juros, pagamento, passivoFinal, ativoBruto: totalVP, deprecAcum: deprecAcumulada, ativoLiquido: totalVP - deprecAcumulada, despJuros: juros, despDeprec: deprecMensal, despTotal: juros + deprecMensal });
        passivoAtual = passivoFinal;
    }

    const cpLp = contabilizacao.map((item, index) => {
        let cp = 0;
        if (index === 0) {
            for (let i = 1; i <= Math.min(12, inputs.prazoMeses); i++) cp += contabilizacao[i].pagamento - contabilizacao[i].juros;
        } else {
            const mesesCP = Math.min(12, inputs.prazoMeses - item.mes);
            for (let i = 1; i <= mesesCP; i++) if (index + i < contabilizacao.length) cp += contabilizacao[index + i].pagamento - contabilizacao[index + i].juros;
        }
        return { ...item, passivoCP: Math.min(item.passivoFinal, Math.max(0, cp)), passivoLP: Math.max(0, item.passivoFinal - cp) };
    });

    const totalJuros = contabilizacao.reduce((s, i) => s + i.juros, 0);
    const totalPagamentos = contabilizacao.reduce((s, i) => s + i.pagamento, 0);
    dadosCalculados = { inputs, taxaMensal, fluxoCaixa, contabilizacao: cpLp, cpLp, totalNominal, totalVP, avp: totalNominal - totalVP, totalJuros, totalPagamentos, totalDeprec: deprecMensal * inputs.prazoMeses, deprecMensal };

    // Mostrar botão de arquivar se houver contrato selecionado
    const btnArquivar = document.getElementById('btnArquivarVersao');
    if (btnArquivar && currentContractId) {
        btnArquivar.classList.remove('hidden');
    }

    document.getElementById('cardPassivo').textContent = 'R$ ' + formatMoney(totalVP);
    document.getElementById('cardAtivo').textContent = 'R$ ' + formatMoney(totalVP);
    document.getElementById('cardNominal').textContent = 'R$ ' + formatMoney(totalNominal);
    document.getElementById('cardAVP').textContent = 'R$ ' + formatMoney(totalNominal - totalVP);
    document.getElementById('cardTotal').textContent = 'R$ ' + formatMoney(totalVP);
    document.getElementById('cardCP').textContent = 'R$ ' + formatMoney(cpLp[0]?.passivoCP || 0);
    document.getElementById('cardLP').textContent = 'R$ ' + formatMoney(cpLp[0]?.passivoLP || 0);

    renderizarResumo();
    renderizarFluxo();
    renderizarContabil();
    renderizarCPLP();
    renderizarLancamentos();
}

function renderizarResumo() {
    const d = dadosCalculados;
    let parcelas = '';
    let ultimaParcela = 0;
    d.fluxoCaixa.forEach(f => {
        if (f.parcela > 0 && Math.abs(f.parcela - ultimaParcela) > 0.01) {
            parcelas += `<div class="glass-card-light px-4 py-2 rounded-lg"><span class="text-dark-400 text-sm">${f.data}:</span><span class="text-white font-semibold ml-2 font-mono">R$ ${formatMoney(f.parcela)}</span></div>`;
            ultimaParcela = f.parcela;
        }
    });
    document.getElementById('conteudo-resumo').innerHTML = `
        <div class="space-y-8">
            <div>
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    Lançamento de Reconhecimento Inicial
                </h3>
                <div class="overflow-x-auto">
                    <table class="table-dark w-full max-w-2xl rounded-lg overflow-hidden">
                        <thead><tr><th class="text-left">Conta</th><th class="text-right">Débito (R$)</th><th class="text-right">Crédito (R$)</th></tr></thead>
                        <tbody>
                            <tr><td class="text-dark-200">D - Ativo de Direito de Uso</td><td class="text-right font-mono text-emerald-400">${formatMoney(d.totalVP)}</td><td></td></tr>
                            <tr><td class="text-dark-200">C - Passivo de Arrendamento (CP)</td><td></td><td class="text-right font-mono text-rose-400">${formatMoney(d.contabilizacao[0]?.passivoCP || 0)}</td></tr>
                            <tr><td class="text-dark-200">C - Passivo de Arrendamento (LP)</td><td></td><td class="text-right font-mono text-rose-400">${formatMoney(d.contabilizacao[0]?.passivoLP || 0)}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div>
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                    Totais ao Longo do Contrato
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="glass-card-light p-4 rounded-xl"><p class="text-dark-400 text-xs uppercase tracking-wider mb-1">Total Juros</p><p class="text-white font-semibold font-mono">R$ ${formatMoney(d.totalJuros)}</p></div>
                    <div class="glass-card-light p-4 rounded-xl"><p class="text-dark-400 text-xs uppercase tracking-wider mb-1">Total Pagamentos</p><p class="text-white font-semibold font-mono">R$ ${formatMoney(d.totalPagamentos)}</p></div>
                    <div class="glass-card-light p-4 rounded-xl"><p class="text-dark-400 text-xs uppercase tracking-wider mb-1">Total Depreciação</p><p class="text-white font-semibold font-mono">R$ ${formatMoney(d.totalDeprec)}</p></div>
                    <div class="glass-card-light p-4 rounded-xl"><p class="text-dark-400 text-xs uppercase tracking-wider mb-1">Depreciação Mensal</p><p class="text-white font-semibold font-mono">R$ ${formatMoney(d.deprecMensal)}</p></div>
                </div>
            </div>
            <div>
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    Evolução das Parcelas
                </h3>
                <div class="flex flex-wrap gap-3">${parcelas}</div>
            </div>
        </div>`;
}

function renderizarFluxo() {
    const d = dadosCalculados;
    let rows = d.fluxoCaixa.map((item, idx) => `<tr><td class="text-center">${item.mes}</td><td class="text-center">${item.data}</td><td class="text-right font-mono">${formatMoney(item.parcela)}</td><td class="text-right font-mono text-dark-400">${item.fatorDesconto.toFixed(6)}</td><td class="text-right font-mono text-primary-400">${formatMoney(item.valorPresente)}</td></tr>`).join('');
    document.getElementById('conteudo-fluxo').innerHTML = `<div class="overflow-x-auto"><table class="table-dark w-full rounded-lg overflow-hidden"><thead><tr><th class="text-center">Mês</th><th class="text-center">Data</th><th class="text-right">Parcela (R$)</th><th class="text-right">Fator Desconto</th><th class="text-right">Valor Presente (R$)</th></tr></thead><tbody>${rows}<tr class="!bg-primary-900/20"><td colspan="2" class="font-bold text-white">TOTAL</td><td class="text-right font-mono font-bold text-white">${formatMoney(d.totalNominal)}</td><td></td><td class="text-right font-mono font-bold text-primary-400">${formatMoney(d.totalVP)}</td></tr></tbody></table></div>`;
}

function renderizarContabil() {
    const d = dadosCalculados;
    let rows = d.contabilizacao.map((item, idx) => `<tr><td class="text-center">${item.mes}</td><td class="text-center">${item.data}</td><td class="text-right font-mono text-xs">${formatMoney(item.passivoInicial)}</td><td class="text-right font-mono text-xs text-amber-400">${formatMoney(item.juros)}</td><td class="text-right font-mono text-xs">${formatMoney(item.pagamento)}</td><td class="text-right font-mono text-xs">${formatMoney(item.passivoFinal)}</td><td class="text-right font-mono text-xs text-rose-400">${formatMoney(item.passivoCP)}</td><td class="text-right font-mono text-xs text-purple-400">${formatMoney(item.passivoLP)}</td><td class="text-right font-mono text-xs text-emerald-400">${formatMoney(item.ativoLiquido)}</td><td class="text-right font-mono text-xs">${formatMoney(item.despTotal)}</td></tr>`).join('');
    document.getElementById('conteudo-contabil').innerHTML = `<div class="overflow-x-auto"><table class="table-dark w-full rounded-lg overflow-hidden text-sm"><thead><tr><th class="text-center">Mês</th><th class="text-center">Data</th><th class="text-right">Pass.Inicial</th><th class="text-right">Juros</th><th class="text-right">Pagamento</th><th class="text-right">Pass.Final</th><th class="text-right">CP</th><th class="text-right">LP</th><th class="text-right">Ativo Líq.</th><th class="text-right">Desp.Total</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function renderizarCPLP() {
    const d = dadosCalculados;
    let rows = d.contabilizacao.map((item, idx) => `<tr><td class="text-center">${item.mes}</td><td class="text-center">${item.data}</td><td class="text-right font-mono">${formatMoney(item.passivoFinal)}</td><td class="text-right font-mono text-rose-400">${formatMoney(item.passivoCP)}</td><td class="text-right font-mono text-purple-400">${formatMoney(item.passivoLP)}</td></tr>`).join('');
    document.getElementById('conteudo-cplp').innerHTML = `<div class="overflow-x-auto"><table class="table-dark w-full rounded-lg overflow-hidden"><thead><tr><th class="text-center">Mês</th><th class="text-center">Data</th><th class="text-right">Passivo Total</th><th class="text-right">Curto Prazo (≤12m)</th><th class="text-right">Longo Prazo (>12m)</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function renderizarLancamentos() {
    const d = dadosCalculados;
    const itensMes = d.contabilizacao.slice(1);
    const parseDateAny = (value) => {
        if (!value) return null;
        if (value instanceof Date && !Number.isNaN(value.getTime())) return value;
        if (typeof value !== 'string') return null;
        const iso = value.match(/^\d{4}-\d{2}-\d{2}$/);
        if (iso) {
            const dt = new Date(value + 'T00:00:00');
            return Number.isNaN(dt.getTime()) ? null : dt;
        }
        const mesAno = value.match(/^(\d{2})\/(\d{4})$/);
        if (mesAno) {
            const dt = new Date(`${mesAno[2]}-${mesAno[1]}-01T00:00:00`);
            return Number.isNaN(dt.getTime()) ? null : dt;
        }
        const br = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
        if (br) {
            const dt = new Date(`${br[3]}-${br[2]}-${br[1]}T00:00:00`);
            return Number.isNaN(dt.getTime()) ? null : dt;
        }
        const dt = new Date(value);
        return Number.isNaN(dt.getTime()) ? null : dt;
    };

    const getCompetenciasCliente = () => {
        let contratos = [];
        if (Array.isArray(window.contractsData)) {
            contratos = window.contractsData;
        } else if (typeof contractsData !== 'undefined' && Array.isArray(contractsData)) {
            contratos = contractsData;
        }
        const ranges = contratos
            .map(c => c?.last_version)
            .filter(v => v && v.data_inicio && v.prazo_meses);

        if (!ranges.length) return [];

        let minStart = null;
        let maxEnd = null;

        for (const v of ranges) {
            const start = parseDateAny(v.data_inicio);
            const prazo = parseInt(v.prazo_meses, 10);
            if (!start || !prazo || prazo < 1) continue;
            const startMonth = new Date(start);
            startMonth.setDate(1);
            const endMonth = new Date(startMonth);
            endMonth.setMonth(endMonth.getMonth() + prazo - 1);
            if (!minStart || startMonth < minStart) minStart = startMonth;
            if (!maxEnd || endMonth > maxEnd) maxEnd = endMonth;
        }

        if (!minStart || !maxEnd) return [];

        const out = [];
        const cursor = new Date(minStart);
        cursor.setDate(1);
        const end = new Date(maxEnd);
        end.setDate(1);
        while (cursor <= end) {
            out.push(formatDataMes(cursor));
            cursor.setMonth(cursor.getMonth() + 1);
        }
        return out;
    };

    const competenciasContratoAtual = Array.from(new Set(itensMes.map(i => i.data)));
    const competencias = getCompetenciasCliente();
    const competenciasFinal = competencias.length ? competencias : competenciasContratoAtual;

    const defaultCompetencia = competenciasContratoAtual[0] || competenciasFinal[0] || '';
    const competenciaSelecionada = (window.lancamentosCompetencia && competenciasFinal.includes(window.lancamentosCompetencia))
        ? window.lancamentosCompetencia
        : defaultCompetencia;

    const itemSel = itensMes.find(i => i.data === competenciaSelecionada);
    const valorJuros = itemSel ? (itemSel.despJuros ?? 0) : 0;
    const valorDeprec = itemSel ? (itemSel.despDeprec ?? 0) : 0;
    const valorPagamento = itemSel ? (itemSel.pagamento ?? 0) : 0;
    const temLancamentosNoContratoAtual = Boolean(itemSel);

    const competenciaPertenceAlgumContratoCadastrado = (() => {
        let contratos = [];
        if (Array.isArray(window.contractsData)) {
            contratos = window.contractsData;
        } else if (typeof contractsData !== 'undefined' && Array.isArray(contractsData)) {
            contratos = contractsData;
        }
        if (!contratos.length) return true;

        const comp = parseDateAny(competenciaSelecionada);
        if (!comp) return true;
        comp.setDate(1);

        for (const c of contratos) {
            const v = c?.last_version;
            if (!v?.data_inicio || !v?.prazo_meses) continue;
            const start = parseDateAny(v.data_inicio);
            const prazo = parseInt(v.prazo_meses, 10);
            if (!start || !prazo || prazo < 1) continue;
            const startMonth = new Date(start);
            startMonth.setDate(1);
            const endMonth = new Date(startMonth);
            endMonth.setMonth(endMonth.getMonth() + prazo - 1);
            if (comp >= startMonth && comp <= endMonth) return true;
        }
        return false;
    })();
    let rows = itensMes.map((item, idx) => `<tr><td class="text-center">${item.mes}</td><td class="text-center">${item.data}</td><td class="text-right font-mono text-xs text-rose-400">${formatMoney(item.despJuros)}</td><td class="text-right font-mono text-xs text-emerald-400">${formatMoney(item.despJuros)}</td><td class="text-right font-mono text-xs text-rose-400">${formatMoney(item.despDeprec)}</td><td class="text-right font-mono text-xs text-emerald-400">${formatMoney(item.despDeprec)}</td><td class="text-right font-mono text-xs text-rose-400">${formatMoney(item.pagamento)}</td><td class="text-right font-mono text-xs text-emerald-400">${formatMoney(item.pagamento)}</td></tr>`).join('');
    document.getElementById('conteudo-lancamentos').innerHTML = `
        <div class="glass-card-light rounded-xl p-4 mb-6">
            <p class="text-primary-400 font-semibold mb-2">Lançamentos Mensais:</p>
            <div class="text-dark-300 text-sm space-y-1">
                <p>1) Juros: <span class="text-rose-400">D-Despesa Financeira</span> / <span class="text-emerald-400">C-Passivo</span></p>
                <p>2) Depreciação: <span class="text-rose-400">D-Despesa Depreciação</span> / <span class="text-emerald-400">C-Deprec.Acumulada</span></p>
                <p>3) Pagamento: <span class="text-rose-400">D-Passivo</span> / <span class="text-emerald-400">C-Caixa</span></p>
            </div>
        </div>
        <div class="glass-card-light rounded-xl p-4 mb-6">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div>
                    <p class="text-dark-300 text-sm">Competência</p>
                    <p class="text-white font-semibold">${competenciaSelecionada || '-'}</p>
                </div>
                <div class="min-w-[220px]">
                    <select id="selectCompetenciaLancamentos" class="w-full bg-dark-900/60 border border-dark-700 rounded-lg px-3 py-2 text-white text-sm">
                        ${competenciasFinal.map(c => `<option value="${c}" ${c === competenciaSelecionada ? 'selected' : ''}>${c}</option>`).join('')}
                    </select>
                </div>
            </div>
            ${!competenciaPertenceAlgumContratoCadastrado
                ? `<p class="text-rose-300 text-sm mt-3">Competência não corresponde a nenhum contrato cadastrado.</p>`
                : (temLancamentosNoContratoAtual ? '' : `<p class="text-amber-300 text-sm mt-3">Sem lançamentos para esta competência no contrato selecionado.</p>`)
            }
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div class="glass-card rounded-xl p-4">
                    <p class="text-primary-400 font-semibold mb-2">1) Juros</p>
                    <div class="text-dark-300 text-sm space-y-1">
                        <p><span class="text-rose-400">D-Despesa Financeira</span> <span class="text-dark-500">(R$)</span></p>
                        <p><span class="text-emerald-400">C-Passivo</span> <span class="text-dark-500">(R$)</span></p>
                    </div>
                    <p class="mt-3 text-white font-mono text-lg">R$ ${formatMoney(valorJuros)}</p>
                </div>
                <div class="glass-card rounded-xl p-4">
                    <p class="text-primary-400 font-semibold mb-2">2) Depreciação</p>
                    <div class="text-dark-300 text-sm space-y-1">
                        <p><span class="text-rose-400">D-Despesa Depreciação</span> <span class="text-dark-500">(R$)</span></p>
                        <p><span class="text-emerald-400">C-Deprec.Acumulada</span> <span class="text-dark-500">(R$)</span></p>
                    </div>
                    <p class="mt-3 text-white font-mono text-lg">R$ ${formatMoney(valorDeprec)}</p>
                </div>
                <div class="glass-card rounded-xl p-4">
                    <p class="text-primary-400 font-semibold mb-2">3) Pagamento</p>
                    <div class="text-dark-300 text-sm space-y-1">
                        <p><span class="text-rose-400">D-Passivo</span> <span class="text-dark-500">(R$)</span></p>
                        <p><span class="text-emerald-400">C-Caixa</span> <span class="text-dark-500">(R$)</span></p>
                    </div>
                    <p class="mt-3 text-white font-mono text-lg">R$ ${formatMoney(valorPagamento)}</p>
                </div>
            </div>
        </div>
        <div class="overflow-x-auto"><table class="table-dark w-full rounded-lg overflow-hidden text-sm"><thead><tr><th class="text-center">Mês</th><th class="text-center">Data</th><th class="text-right">D-Desp.Fin.</th><th class="text-right">C-Passivo</th><th class="text-right">D-Deprec.</th><th class="text-right">C-Dep.Ac.</th><th class="text-right">D-Passivo</th><th class="text-right">C-Caixa</th></tr></thead><tbody>${rows}<tr class="!bg-primary-900/20"><td colspan="2" class="font-bold text-white">TOTAIS</td><td class="text-right font-mono text-xs font-bold">${formatMoney(d.totalJuros)}</td><td class="text-right font-mono text-xs font-bold">${formatMoney(d.totalJuros)}</td><td class="text-right font-mono text-xs font-bold">${formatMoney(d.totalDeprec)}</td><td class="text-right font-mono text-xs font-bold">${formatMoney(d.totalDeprec)}</td><td class="text-right font-mono text-xs font-bold">${formatMoney(d.totalPagamentos)}</td><td class="text-right font-mono text-xs font-bold">${formatMoney(d.totalPagamentos)}</td></tr></tbody></table></div>`;

    const select = document.getElementById('selectCompetenciaLancamentos');
    if (select) {
        select.addEventListener('change', (e) => {
            window.lancamentosCompetencia = e.target.value;
            renderizarLancamentos();
        });
    }
}
