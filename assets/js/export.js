// ============================================================
// FUNÇÕES DE EXPORTAÇÃO
// ============================================================

async function exportarExcel() {
    const d = dadosCalculados;
    const workbook = new ExcelJS.Workbook();
    workbook.creator = 'Fernando Xavier - Repositório IFRS 16';
    workbook.created = new Date();
    const headerStyle = { font: { bold: true, color: { argb: 'FFFFFFFF' }, size: 11 }, fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF166534' } }, alignment: { horizontal: 'center' } };
    const moneyFormat = '#,##0.00';

    const wsPremissas = workbook.addWorksheet('Premissas');
    wsPremissas.mergeCells('B2:D2');
    wsPremissas.getCell('B2').value = 'IFRS 16 - PREMISSAS DO CONTRATO';
    wsPremissas.getCell('B2').font = { bold: true, size: 14, color: { argb: 'FF166534' } };
    [['Início', d.inputs.dataInicio.toLocaleDateString('pt-BR')], ['Prazo (meses)', d.inputs.prazoMeses], ['Carência (meses)', d.inputs.carenciaMeses], ['Taxa Anual', d.inputs.taxaAnual / 100], ['Taxa Mensal', d.taxaMensal], ['Reajuste Anual', d.inputs.reajusteAnual / 100], ['Parcela Inicial', d.inputs.parcelaInicial]].forEach((row, idx) => {
        wsPremissas.getCell(`B${idx + 4}`).value = row[0];
        wsPremissas.getCell(`C${idx + 4}`).value = row[1];
        if (idx >= 3 && idx <= 5) wsPremissas.getCell(`C${idx + 4}`).numFmt = '0.0000%';
        if (idx === 6) wsPremissas.getCell(`C${idx + 4}`).numFmt = moneyFormat;
    });
    wsPremissas.getCell('B13').value = '© 2025 Fernando Xavier - Licença: ' + licencaAtiva;
    wsPremissas.getCell('B13').font = { italic: true, size: 9 };
    wsPremissas.getColumn('B').width = 25;
    wsPremissas.getColumn('C').width = 20;

    const wsFluxo = workbook.addWorksheet('Fluxo de Caixa');
    wsFluxo.addRow([]);
    const hFluxo = wsFluxo.addRow(['Mês', 'Data', 'Parcela', 'Fator', 'VP']);
    hFluxo.eachCell(c => { c.font = headerStyle.font; c.fill = headerStyle.fill; });
    d.fluxoCaixa.forEach(item => {
        const row = wsFluxo.addRow([item.mes, item.data, item.parcela, item.fatorDesconto, item.valorPresente]);
        row.getCell(3).numFmt = moneyFormat;
        row.getCell(5).numFmt = moneyFormat;
    });
    const tFluxo = wsFluxo.addRow(['', 'TOTAL', d.totalNominal, '', d.totalVP]);
    tFluxo.font = { bold: true };
    tFluxo.getCell(3).numFmt = moneyFormat;
    tFluxo.getCell(5).numFmt = moneyFormat;
    [8, 12, 16, 14, 16].forEach((w, i) => wsFluxo.getColumn(i + 1).width = w);

    const wsContab = workbook.addWorksheet('Contabilização');
    wsContab.addRow([]);
    const hContab = wsContab.addRow(['Mês', 'Data', 'Pass.Ini', 'Juros', 'Pagto', 'Pass.Fin', 'CP', 'LP', 'Ativo', 'Desp.Total']);
    hContab.eachCell(c => { c.font = headerStyle.font; c.fill = headerStyle.fill; });
    d.contabilizacao.forEach(item => {
        const row = wsContab.addRow([item.mes, item.data, item.passivoInicial, item.juros, item.pagamento, item.passivoFinal, item.passivoCP, item.passivoLP, item.ativoLiquido, item.despTotal]);
        for (let i = 3; i <= 10; i++) row.getCell(i).numFmt = moneyFormat;
    });
    for (let i = 1; i <= 10; i++) wsContab.getColumn(i).width = 14;

    const wsLanc = workbook.addWorksheet('Lançamentos');
    wsLanc.addRow([]);
    const hLanc = wsLanc.addRow(['Mês', 'Data', 'D-Desp.Fin', 'C-Passivo', 'D-Deprec', 'C-Dep.Ac', 'D-Passivo', 'C-Caixa']);
    hLanc.eachCell(c => { c.font = headerStyle.font; c.fill = headerStyle.fill; });
    d.contabilizacao.slice(1).forEach(item => {
        const row = wsLanc.addRow([item.mes, item.data, item.despJuros, item.despJuros, item.despDeprec, item.despDeprec, item.pagamento, item.pagamento]);
        for (let i = 3; i <= 8; i++) row.getCell(i).numFmt = moneyFormat;
    });
    const tLanc = wsLanc.addRow(['', 'TOTAIS', d.totalJuros, d.totalJuros, d.totalDeprec, d.totalDeprec, d.totalPagamentos, d.totalPagamentos]);
    tLanc.font = { bold: true };
    for (let i = 3; i <= 8; i++) tLanc.getCell(i).numFmt = moneyFormat;
    for (let i = 1; i <= 8; i++) wsLanc.getColumn(i).width = 14;

    const wsResumo = workbook.addWorksheet('Resumo');
    wsResumo.getCell('B2').value = 'RESUMO EXECUTIVO - IFRS 16';
    wsResumo.getCell('B2').font = { bold: true, size: 14 };
    [['Passivo (VP)', d.totalVP], ['Passivo CP', d.contabilizacao[0].passivoCP], ['Passivo LP', d.contabilizacao[0].passivoLP], ['Ativo DDU', d.totalVP], ['Total Nominal', d.totalNominal], ['AVP', d.avp], ['Total Juros', d.totalJuros], ['Total Pagtos', d.totalPagamentos], ['Total Deprec', d.totalDeprec]].forEach((row, idx) => {
        wsResumo.getCell(`B${idx + 4}`).value = row[0];
        wsResumo.getCell(`C${idx + 4}`).value = row[1];
        wsResumo.getCell(`C${idx + 4}`).numFmt = moneyFormat;
    });
    wsResumo.getCell('B15').value = '© 2025 Fernando Xavier | Licença: ' + licencaAtiva + ' | ' + new Date().toLocaleString('pt-BR');
    wsResumo.getCell('B15').font = { italic: true, size: 9 };
    wsResumo.getColumn('B').width = 20;
    wsResumo.getColumn('C').width = 20;

    const buffer = await workbook.xlsx.writeBuffer();
    saveAs(new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }), `IFRS16_${d.inputs.dataInicio.toISOString().slice(0, 10)}_${d.inputs.prazoMeses}m.xlsx`);
}

function exportarCSV() {
    const d = dadosCalculados;
    let csv = 'Mês;Data;Pass.Ini;Juros;Pagto;Pass.Fin;CP;LP;Ativo;Desp.Total\n';
    d.contabilizacao.forEach(i => csv += `${i.mes};${i.data};${i.passivoInicial.toFixed(2)};${i.juros.toFixed(2)};${i.pagamento.toFixed(2)};${i.passivoFinal.toFixed(2)};${i.passivoCP.toFixed(2)};${i.passivoLP.toFixed(2)};${i.ativoLiquido.toFixed(2)};${i.despTotal.toFixed(2)}\n`);
    csv += `\n© 2025 Fernando Xavier | Licença: ${licencaAtiva}`;
    saveAs(new Blob([csv], { type: 'text/csv;charset=utf-8;' }), 'IFRS16_Contabilizacao.csv');
}
