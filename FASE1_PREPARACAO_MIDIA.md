# 📸 FASE 1: PREPARAÇÃO DE MÍDIA - GUIA PRÁTICO

**Status:** Em Andamento  
**Prazo:** 1-2 dias  
**Objetivo:** Capturar e organizar todo o conteúdo visual da calculadora

---

## ✅ CHECKLIST DA FASE 1

### 1. Estrutura de Pastas
- [x] Criar estrutura de diretórios
- [ ] Configurar Firebase Storage
- [ ] Definir convenção de nomenclatura

### 2. Capturas de Tela
- [ ] Dashboard principal
- [ ] Tela de contratos
- [ ] Formulário de novo contrato
- [ ] Calculadora em ação
- [ ] Relatório gerado
- [ ] Gráficos e visualizações
- [ ] Exportação Excel

### 3. Vídeo Demo
- [ ] Roteiro do vídeo (30s)
- [ ] Gravação com OBS Studio
- [ ] Edição básica
- [ ] Compressão

### 4. GIFs Animados
- [ ] Criação de contrato
- [ ] Cálculo automático
- [ ] Geração de relatório
- [ ] Exportação Excel

---

## 📁 ESTRUTURA DE PASTAS CRIADA

```
/media
  /screenshots
    - dashboard.png
    - contratos-lista.png
    - contrato-novo.png
    - calculadora-resultado.png
    - relatorio-pdf.png
    - graficos.png
    - exportacao-excel.png
  /videos
    - demo-30s.mp4
    - tutorial-completo.mp4
  /gifs
    - criacao-contrato.gif
    - calculo-automatico.gif
    - geracao-relatorio.gif
    - exportacao-excel.gif
  /thumbnails
    - demo-thumb.jpg
```

---

## 📸 GUIA DE CAPTURA DE SCREENSHOTS

### Preparação
1. **Abrir a calculadora em produção:**
   - URL: https://fxstudioai.com
   - Fazer login com sua conta
   - Ter alguns contratos de exemplo criados

2. **Configurar navegador:**
   - Zoom: 100%
   - Resolução: 1920x1080 (Full HD)
   - Modo: Tela cheia (F11)
   - DevTools: Fechado

3. **Ferramenta de captura:**
   - **Windows:** Win + Shift + S (Snipping Tool)
   - **Chrome DevTools:** F12 → Cmd/Ctrl + Shift + P → "Screenshot"
   - **ShareX:** Recomendado para capturas rápidas

---

### Screenshot 1: Dashboard Principal
**Arquivo:** `dashboard.png`

**O que capturar:**
- Header com logo e menu
- Seção "Minha Conta" com dados do usuário
- Cards de estatísticas (se houver)
- Lista de contratos recentes
- Botões de ação principais

**Dicas:**
- Certifique-se de ter dados reais visíveis
- Evite informações sensíveis (use dados fictícios)
- Capture a tela inteira, não apenas uma parte

**Atalho Chrome DevTools:**
1. F12
2. Ctrl + Shift + P
3. Digite "Capture full size screenshot"
4. Enter

---

### Screenshot 2: Lista de Contratos
**Arquivo:** `contratos-lista.png`

**O que capturar:**
- Tabela completa de contratos
- Colunas: Nome, Código, Valor, Status, Data
- Botões de ação (Editar, Visualizar, Deletar)
- Filtros e busca (se houver)
- Paginação

**Dicas:**
- Tenha pelo menos 5-7 contratos visíveis
- Mostre diferentes status (ACTIVE, DRAFT)
- Capture com scroll no topo

---

### Screenshot 3: Formulário de Novo Contrato
**Arquivo:** `contrato-novo.png`

**O que capturar:**
- Formulário completo de cadastro
- Campos preenchidos com dados de exemplo
- Labels e placeholders visíveis
- Botões de ação (Salvar, Cancelar)

**Dicas:**
- Preencha todos os campos com dados realistas
- Mostre validações (se houver)
- Capture antes de submeter

---

### Screenshot 4: Calculadora em Ação
**Arquivo:** `calculadora-resultado.png`

**O que capturar:**
- Inputs do contrato
- Resultados dos cálculos
- Tabela de amortização
- Gráficos (se visíveis)
- Valores destacados

**Dicas:**
- Use valores que gerem resultados interessantes
- Mostre a tabela completa (ou parte significativa)
- Destaque os valores principais

---

### Screenshot 5: Relatório Gerado
**Arquivo:** `relatorio-pdf.png`

**O que capturar:**
- Preview do PDF gerado
- Cabeçalho com logo e título
- Tabelas de dados
- Gráficos incluídos
- Rodapé com informações

**Dicas:**
- Capture a primeira página completa
- Mostre a qualidade profissional
- Se possível, capture em modo "preview"

---

### Screenshot 6: Gráficos e Visualizações
**Arquivo:** `graficos.png`

**O que capturar:**
- Gráficos de evolução
- Visualizações de dados
- Legendas e labels
- Cores e estilo

**Dicas:**
- Capture gráficos com dados reais
- Mostre diferentes tipos de visualização
- Certifique-se de que as legendas estão legíveis

---

### Screenshot 7: Exportação Excel
**Arquivo:** `exportacao-excel.png`

**O que capturar:**
- Botão de exportação
- Modal de confirmação (se houver)
- Preview do arquivo Excel (opcional)

**Dicas:**
- Capture o momento antes do download
- Mostre o botão destacado
- Se possível, mostre o arquivo Excel aberto

---

## 🎬 GUIA DE GRAVAÇÃO DE VÍDEO

### Vídeo 1: Demo Rápida (30 segundos)

**Roteiro:**
1. **0-5s:** Mostrar dashboard (zoom out)
2. **5-10s:** Clicar em "Novo Contrato"
3. **10-15s:** Preencher formulário rapidamente
4. **15-20s:** Mostrar resultado do cálculo
5. **20-25s:** Gerar relatório PDF
6. **25-30s:** Mostrar PDF gerado + CTA

**Ferramentas:**
- **OBS Studio** (grátis, profissional)
- **Loom** (fácil, online)

**Configurações OBS:**
```
Resolução: 1280x720 (HD)
FPS: 30
Bitrate: 2500 kbps
Formato: MP4
Codec: H.264
```

**Passos:**
1. Abrir OBS Studio
2. Adicionar fonte: "Captura de Janela" (navegador)
3. Ajustar área de captura
4. Iniciar gravação
5. Seguir roteiro
6. Parar gravação
7. Salvar em `media/videos/demo-30s-raw.mp4`

---

### Vídeo 2: Tutorial Completo (2-3 minutos)

**Roteiro:**
1. **Introdução (15s):** Apresentar a calculadora
2. **Cadastro (30s):** Criar novo contrato passo a passo
3. **Cálculo (45s):** Mostrar resultados e explicar
4. **Relatório (30s):** Gerar e mostrar PDF
5. **Exportação (20s):** Exportar para Excel
6. **Conclusão (10s):** CTA e benefícios

---

## 🎞️ GUIA DE CRIAÇÃO DE GIFs

### GIF 1: Criação de Contrato
**Arquivo:** `criacao-contrato.gif`  
**Duração:** 3-5 segundos

**Passos:**
1. Abrir ScreenToGif
2. Selecionar área (formulário)
3. Iniciar gravação
4. Preencher campos rapidamente
5. Clicar em "Salvar"
6. Parar gravação
7. Editar: remover frames desnecessários
8. Exportar: < 2MB

**Ferramenta:** ScreenToGif (Windows)
- Download: screentogif.com
- Grátis e fácil de usar

---

### GIF 2: Cálculo Automático
**Arquivo:** `calculo-automatico.gif`  
**Duração:** 3-4 segundos

**O que mostrar:**
- Input de dados
- Clique em "Calcular"
- Resultados aparecendo (animação)

---

### GIF 3: Geração de Relatório
**Arquivo:** `geracao-relatorio.gif`  
**Duração:** 3-4 segundos

**O que mostrar:**
- Clique em "Gerar Relatório"
- Loading/processamento
- PDF aparecendo

---

### GIF 4: Exportação Excel
**Arquivo:** `exportacao-excel.gif`  
**Duração:** 2-3 segundos

**O que mostrar:**
- Clique em "Exportar Excel"
- Ícone de download
- Arquivo baixado

---

## 🔧 FERRAMENTAS NECESSÁRIAS

### Captura de Tela
- ✅ **Windows Snipping Tool** (nativo)
- ✅ **ShareX** (grátis, avançado)
- ✅ **Chrome DevTools** (F12)

### Gravação de Vídeo
- ✅ **OBS Studio** (grátis, profissional)
  - Download: obsproject.com
- ⚠️ **Loom** (fácil, mas pago após 25 vídeos)

### Criação de GIFs
- ✅ **ScreenToGif** (Windows, grátis)
  - Download: screentogif.com
- ✅ **Gifox** (Mac, $15)

### Edição
- ✅ **DaVinci Resolve** (grátis, profissional)
- ✅ **iMovie** (Mac, grátis)

---

## 📊 CONVENÇÃO DE NOMENCLATURA

### Screenshots
```
[tipo]-[descricao].png

Exemplos:
- dashboard-principal.png
- contratos-lista.png
- contrato-novo-form.png
- calculadora-resultado.png
- relatorio-pdf-preview.png
```

### Vídeos
```
[tipo]-[duracao].mp4

Exemplos:
- demo-30s.mp4
- tutorial-completo-2min.mp4
```

### GIFs
```
[acao]-[descricao].gif

Exemplos:
- criacao-contrato.gif
- calculo-automatico.gif
- geracao-relatorio.gif
```

---

## ⏱️ CRONOGRAMA SUGERIDO

### Dia 1 (4 horas)
- **Manhã (2h):**
  - Instalar ferramentas (OBS, ScreenToGif)
  - Preparar ambiente (dados de exemplo)
  - Capturar 7 screenshots principais

- **Tarde (2h):**
  - Gravar vídeo demo 30s (3-5 takes)
  - Criar 4 GIFs animados
  - Organizar arquivos na estrutura de pastas

### Dia 2 (2 horas)
- **Manhã (1h):**
  - Gravar tutorial completo (2-3min)
  - Edição básica do vídeo

- **Tarde (1h):**
  - Revisar todo o material
  - Verificar qualidade
  - Preparar para Fase 2 (otimização)

---

## ✅ CRITÉRIOS DE QUALIDADE

### Screenshots
- ✅ Resolução mínima: 1280x720
- ✅ Formato: PNG (original)
- ✅ Sem informações sensíveis
- ✅ Interface limpa e organizada
- ✅ Dados realistas e profissionais

### Vídeos
- ✅ Resolução: 1280x720 (HD)
- ✅ FPS: 30
- ✅ Áudio: Opcional (música de fundo suave)
- ✅ Duração: Conforme roteiro
- ✅ Sem cortes bruscos

### GIFs
- ✅ Resolução: 800x600 ou menor
- ✅ Duração: 3-5 segundos
- ✅ Loop suave
- ✅ Tamanho: < 2MB (antes da otimização)

---

## 🚀 PRÓXIMOS PASSOS

Após completar a Fase 1:
1. ✅ Revisar todo o material capturado
2. ✅ Verificar se todos os itens do checklist estão completos
3. ✅ Organizar arquivos na estrutura de pastas
4. ➡️ **Avançar para Fase 2: Otimização**

---

## 📝 NOTAS IMPORTANTES

- **Dados fictícios:** Use sempre dados de exemplo, nunca dados reais de clientes
- **Qualidade > Quantidade:** Melhor ter 5 screenshots perfeitos do que 10 medianos
- **Consistência:** Mantenha o mesmo tema/estilo em todas as capturas
- **Backup:** Salve os arquivos originais antes de otimizar

---

**Pronto para começar? Siga este guia passo a passo e terá todo o material necessário para a Fase 2!**
