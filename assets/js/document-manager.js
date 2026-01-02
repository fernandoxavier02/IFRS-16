// ============================================================
// GERENCIADOR DE DOCUMENTOS - IFRS 16
// Upload, listagem e download de documentos
// ============================================================

const DocumentManager = {
    // Configuracao
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_TYPES: ['application/pdf', 'image/jpeg', 'image/png', 'image/gif'],
    ALLOWED_EXTENSIONS: ['.pdf', '.jpg', '.jpeg', '.png', '.gif'],

    // Estado
    currentContractDocuments: [],
    uploadQueue: [],
    isUploading: false,

    // ============================================================
    // API CALLS
    // ============================================================

    getAuthToken() {
        return localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    },

    getApiUrl() {
        if (typeof CONFIG !== 'undefined' && CONFIG.API_URL) {
            return CONFIG.API_URL;
        }
        const hostname = window.location.hostname;
        if (hostname.includes('fxstudioai.com') || hostname.includes('web.app') || hostname.includes('firebaseapp.com')) {
            return 'https://ifrs16-backend-ox4zylcs5a-uc.a.run.app';
        }
        return 'http://localhost:8000';
    },

    async uploadDocument(contractId, file, description = '') {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('Voce precisa estar logado para fazer upload de documentos');
        }

        // Validar arquivo
        this.validateFile(file);

        const formData = new FormData();
        formData.append('file', file);
        if (description) {
            formData.append('description', description);
        }

        const response = await fetch(`${this.getApiUrl()}/api/documents/contracts/${contractId}/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Erro ao fazer upload' }));
            throw new Error(error.detail || 'Erro ao fazer upload do documento');
        }

        return await response.json();
    },

    async getContractDocuments(contractId) {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('Voce precisa estar logado para ver documentos');
        }

        const response = await fetch(`${this.getApiUrl()}/api/documents/contracts/${contractId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 404) {
                return { documents: [], total: 0 };
            }
            const error = await response.json().catch(() => ({ detail: 'Erro ao carregar documentos' }));
            throw new Error(error.detail || 'Erro ao carregar documentos');
        }

        const data = await response.json();
        this.currentContractDocuments = data.documents || [];
        return data;
    },

    async getDocumentDownloadUrl(documentId) {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('Voce precisa estar logado para baixar documentos');
        }

        const response = await fetch(`${this.getApiUrl()}/api/documents/${documentId}/download`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Erro ao obter link de download' }));
            throw new Error(error.detail || 'Erro ao obter link de download');
        }

        return await response.json();
    },

    async deleteDocument(documentId) {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('Voce precisa estar logado para excluir documentos');
        }

        const response = await fetch(`${this.getApiUrl()}/api/documents/${documentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Erro ao excluir documento' }));
            throw new Error(error.detail || 'Erro ao excluir documento');
        }

        return await response.json();
    },

    async updateDocument(documentId, description) {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('Voce precisa estar logado para atualizar documentos');
        }

        const response = await fetch(`${this.getApiUrl()}/api/documents/${documentId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Erro ao atualizar documento' }));
            throw new Error(error.detail || 'Erro ao atualizar documento');
        }

        return await response.json();
    },

    // ============================================================
    // VALIDACAO
    // ============================================================

    validateFile(file) {
        // Verificar tamanho
        if (file.size > this.MAX_FILE_SIZE) {
            const maxMB = this.MAX_FILE_SIZE / (1024 * 1024);
            throw new Error(`Arquivo muito grande. Tamanho maximo: ${maxMB}MB`);
        }

        // Verificar tipo MIME
        if (!this.ALLOWED_TYPES.includes(file.type)) {
            throw new Error(`Tipo de arquivo nao permitido. Tipos aceitos: PDF, JPG, PNG, GIF`);
        }

        // Verificar extensao
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.ALLOWED_EXTENSIONS.includes(extension)) {
            throw new Error(`Extensao de arquivo nao permitida. Extensoes aceitas: ${this.ALLOWED_EXTENSIONS.join(', ')}`);
        }

        return true;
    },

    // ============================================================
    // UI HELPERS
    // ============================================================

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    getFileIcon(mimeType) {
        if (mimeType === 'application/pdf') {
            return `<svg class="w-8 h-8 text-rose-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                <path d="M14 2v6h6"/>
                <path d="M10 12h4" stroke="white" stroke-width="1.5"/>
                <path d="M10 16h4" stroke="white" stroke-width="1.5"/>
            </svg>`;
        }
        if (mimeType.startsWith('image/')) {
            return `<svg class="w-8 h-8 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke-width="2"/>
                <circle cx="8.5" cy="8.5" r="1.5" stroke-width="2"/>
                <polyline points="21 15 16 10 5 21" stroke-width="2"/>
            </svg>`;
        }
        return `<svg class="w-8 h-8 text-dark-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke-width="2"/>
            <polyline points="14 2 14 8 20 8" stroke-width="2"/>
        </svg>`;
    },

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    canPreviewFile(mimeType) {
        const previewableTypes = [
            'application/pdf',
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/gif',
            'image/webp'
        ];
        return previewableTypes.includes(mimeType);
    },

    // ============================================================
    // VISUALIZADOR DE DOCUMENTOS
    // ============================================================

    async previewDocument(documentId, filename, mimeType) {
        try {
            this.showNotification('Carregando documento...', 'info');

            // Obter URL de download
            const data = await this.getDocumentDownloadUrl(documentId);
            const url = data.download_url;

            // Abrir modal de preview
            this.openPreviewModal(url, filename, mimeType);

        } catch (error) {
            this.showNotification('Erro ao carregar documento: ' + error.message, 'error');
        }
    },

    openPreviewModal(url, filename, mimeType) {
        // Remover modal existente se houver
        let modal = document.getElementById('documentPreviewModal');
        if (modal) modal.remove();

        // Criar modal
        modal = document.createElement('div');
        modal.id = 'documentPreviewModal';
        modal.className = 'fixed inset-0 bg-black/90 backdrop-blur-sm z-[100] flex flex-col';

        const isPdf = mimeType === 'application/pdf';
        const isImage = mimeType.startsWith('image/');

        modal.innerHTML = `
            <div class="preview-header flex items-center justify-between p-4 bg-dark-900/80 border-b border-dark-700">
                <div class="flex items-center gap-3">
                    <div class="preview-icon">
                        ${isPdf ? `
                        <svg class="w-6 h-6 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke-width="2"/>
                            <polyline points="14 2 14 8 20 8" stroke-width="2"/>
                            <line x1="16" y1="13" x2="8" y2="13" stroke-width="2"/>
                            <line x1="16" y1="17" x2="8" y2="17" stroke-width="2"/>
                        </svg>
                        ` : `
                        <svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke-width="2"/>
                            <circle cx="8.5" cy="8.5" r="1.5" stroke-width="2"/>
                            <polyline points="21 15 16 10 5 21" stroke-width="2"/>
                        </svg>
                        `}
                    </div>
                    <div>
                        <h3 class="text-white font-medium text-sm truncate max-w-md">${filename}</h3>
                        <p class="text-dark-400 text-xs">${isPdf ? 'Documento PDF' : 'Imagem'}</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button type="button" onclick="DocumentManager.downloadFromPreview('${url}', '${filename.replace(/'/g, "\\'")}')"
                        class="preview-action-btn" title="Baixar">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                        </svg>
                    </button>
                    <button type="button" onclick="DocumentManager.openInNewTab('${url}')"
                        class="preview-action-btn" title="Abrir em nova aba">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                        </svg>
                    </button>
                    <button type="button" onclick="DocumentManager.closePreviewModal()"
                        class="preview-close-btn" title="Fechar (ESC)">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="preview-content flex-1 overflow-hidden flex items-center justify-center p-4">
                ${isPdf ? `
                <iframe
                    src="${url}#toolbar=1&navpanes=0&scrollbar=1&view=FitH"
                    class="w-full h-full rounded-lg border border-dark-700 bg-white"
                    title="${filename}"
                    loading="lazy">
                </iframe>
                ` : `
                <div class="preview-image-container relative max-w-full max-h-full overflow-auto">
                    <img
                        src="${url}"
                        alt="${filename}"
                        class="max-w-full max-h-[calc(100vh-120px)] object-contain rounded-lg shadow-2xl"
                        loading="lazy"
                        onload="this.style.opacity='1'"
                        style="opacity: 0; transition: opacity 0.3s ease;">
                </div>
                `}
            </div>
        `;

        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';

        // Fechar com ESC
        this._previewEscHandler = (e) => {
            if (e.key === 'Escape') {
                this.closePreviewModal();
            }
        };
        document.addEventListener('keydown', this._previewEscHandler);

        // Fechar clicando fora (apenas para imagens)
        if (isImage) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal || e.target.classList.contains('preview-content')) {
                    this.closePreviewModal();
                }
            });
        }
    },

    closePreviewModal() {
        const modal = document.getElementById('documentPreviewModal');
        if (modal) {
            modal.remove();
            document.body.style.overflow = '';
            if (this._previewEscHandler) {
                document.removeEventListener('keydown', this._previewEscHandler);
                this._previewEscHandler = null;
            }
        }
    },

    downloadFromPreview(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    openInNewTab(url) {
        window.open(url, '_blank');
    },

    // ============================================================
    // UI COMPONENTS
    // ============================================================

    createDropZone(containerId, contractId, onUploadComplete) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div id="documentDropZone" class="document-drop-zone">
                <div class="drop-zone-content">
                    <div class="drop-zone-icon">
                        <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                        </svg>
                    </div>
                    <p class="drop-zone-title">Arraste arquivos aqui</p>
                    <p class="drop-zone-subtitle">ou clique para selecionar</p>
                    <p class="drop-zone-info">PDF, JPG, PNG ou GIF (max. 10MB)</p>
                    <input type="file" id="documentFileInput" class="hidden"
                        accept=".pdf,.jpg,.jpeg,.png,.gif" multiple>
                </div>
                <div id="uploadProgress" class="upload-progress hidden">
                    <div class="upload-progress-bar">
                        <div id="uploadProgressFill" class="upload-progress-fill"></div>
                    </div>
                    <p id="uploadProgressText" class="upload-progress-text">Enviando...</p>
                </div>
            </div>
            <div id="documentDescriptionModal" class="document-modal hidden">
                <div class="document-modal-content">
                    <h3 class="document-modal-title">Adicionar Descricao</h3>
                    <p id="documentFileName" class="document-modal-filename"></p>
                    <textarea id="documentDescription" class="document-modal-textarea"
                        placeholder="Descricao do documento (opcional)..." rows="3"></textarea>
                    <div class="document-modal-actions">
                        <button type="button" id="cancelDescriptionBtn" class="btn-secondary-doc">Cancelar</button>
                        <button type="button" id="confirmUploadBtn" class="btn-primary-doc">Enviar Documento</button>
                    </div>
                </div>
            </div>
        `;

        this.initDropZoneEvents(contractId, onUploadComplete);
    },

    initDropZoneEvents(contractId, onUploadComplete) {
        const dropZone = document.getElementById('documentDropZone');
        const fileInput = document.getElementById('documentFileInput');
        const descriptionModal = document.getElementById('documentDescriptionModal');
        const cancelBtn = document.getElementById('cancelDescriptionBtn');
        const confirmBtn = document.getElementById('confirmUploadBtn');

        if (!dropZone || !fileInput) return;

        let pendingFile = null;

        // Click para selecionar arquivo
        dropZone.addEventListener('click', (e) => {
            if (!e.target.closest('.upload-progress') && !this.isUploading) {
                fileInput.click();
            }
        });

        // Eventos de drag & drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0], contractId, onUploadComplete);
            }
        });

        // Selecao de arquivo via input
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0], contractId, onUploadComplete);
            }
        });

        // Modal de descricao
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                descriptionModal.classList.add('hidden');
                pendingFile = null;
                fileInput.value = '';
            });
        }

        if (confirmBtn) {
            confirmBtn.addEventListener('click', async () => {
                if (pendingFile) {
                    const description = document.getElementById('documentDescription').value;
                    descriptionModal.classList.add('hidden');
                    await this.processUpload(pendingFile, contractId, description, onUploadComplete);
                    pendingFile = null;
                    fileInput.value = '';
                }
            });
        }

        // Armazenar referencia para uso no handleFileSelect
        this.pendingFileRef = {
            set: (file) => { pendingFile = file; },
            get: () => pendingFile
        };
    },

    handleFileSelect(file, contractId, onUploadComplete) {
        try {
            this.validateFile(file);

            // Mostrar modal de descricao
            const modal = document.getElementById('documentDescriptionModal');
            const fileName = document.getElementById('documentFileName');
            const description = document.getElementById('documentDescription');

            if (modal && fileName && description) {
                fileName.textContent = `${file.name} (${this.formatFileSize(file.size)})`;
                description.value = '';
                modal.classList.remove('hidden');
                this.pendingFileRef.set(file);
            } else {
                // Se nao houver modal, fazer upload direto
                this.processUpload(file, contractId, '', onUploadComplete);
            }
        } catch (error) {
            this.showNotification(error.message, 'error');
        }
    },

    async processUpload(file, contractId, description, onUploadComplete) {
        const progressContainer = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('uploadProgressFill');
        const progressText = document.getElementById('uploadProgressText');
        const dropContent = document.querySelector('.drop-zone-content');

        try {
            this.isUploading = true;

            if (progressContainer && dropContent) {
                dropContent.classList.add('hidden');
                progressContainer.classList.remove('hidden');
                progressFill.style.width = '0%';
                progressText.textContent = 'Enviando...';
            }

            // Simular progresso (ja que fetch nao suporta progresso de upload nativo)
            let progress = 0;
            const progressInterval = setInterval(() => {
                if (progress < 90) {
                    progress += Math.random() * 15;
                    if (progressFill) progressFill.style.width = `${Math.min(progress, 90)}%`;
                }
            }, 200);

            const result = await this.uploadDocument(contractId, file, description);

            clearInterval(progressInterval);
            if (progressFill) progressFill.style.width = '100%';
            if (progressText) progressText.textContent = 'Concluido!';

            setTimeout(() => {
                if (progressContainer && dropContent) {
                    progressContainer.classList.add('hidden');
                    dropContent.classList.remove('hidden');
                }
                this.isUploading = false;
            }, 1000);

            this.showNotification('Documento enviado com sucesso!', 'success');

            if (onUploadComplete) {
                onUploadComplete(result);
            }

        } catch (error) {
            if (progressContainer && dropContent) {
                progressContainer.classList.add('hidden');
                dropContent.classList.remove('hidden');
            }
            this.isUploading = false;
            this.showNotification(error.message, 'error');
        }
    },

    createDocumentList(containerId, documents, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!documents || documents.length === 0) {
            container.innerHTML = `
                <div class="documents-empty">
                    <svg class="w-12 h-12 text-dark-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <p class="text-dark-400 text-sm">Nenhum documento anexado</p>
                    <p class="text-dark-500 text-xs mt-1">Arraste arquivos para a area acima</p>
                </div>
            `;
            return;
        }

        const html = documents.map(doc => {
            const canPreview = this.canPreviewFile(doc.mime_type);
            return `
            <div class="document-item" data-document-id="${doc.id}">
                <div class="document-icon">
                    ${this.getFileIcon(doc.mime_type)}
                </div>
                <div class="document-info">
                    <p class="document-name" title="${doc.filename}">${doc.filename}</p>
                    <p class="document-meta">
                        ${this.formatFileSize(doc.file_size)} | ${this.formatDate(doc.created_at)}
                    </p>
                    ${doc.description ? `<p class="document-description">${doc.description}</p>` : ''}
                </div>
                <div class="document-actions">
                    ${canPreview ? `
                    <button type="button" class="doc-action-btn doc-view-btn"
                        onclick="DocumentManager.previewDocument('${doc.id}', '${doc.filename.replace(/'/g, "\\'")}', '${doc.mime_type}')" title="Visualizar">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                    </button>
                    ` : ''}
                    <button type="button" class="doc-action-btn doc-download-btn"
                        onclick="DocumentManager.downloadDocument('${doc.id}')" title="Baixar">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                        </svg>
                    </button>
                    ${options.allowDelete !== false ? `
                    <button type="button" class="doc-action-btn doc-delete-btn"
                        onclick="DocumentManager.confirmDelete('${doc.id}', '${doc.filename.replace(/'/g, "\\'")}')" title="Excluir">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                    ` : ''}
                </div>
            </div>
        `;
        }).join('');

        container.innerHTML = `<div class="documents-list">${html}</div>`;
    },

    async downloadDocument(documentId) {
        try {
            this.showNotification('Gerando link de download...', 'info');
            const data = await this.getDocumentDownloadUrl(documentId);

            // Abrir em nova aba
            window.open(data.download_url, '_blank');

        } catch (error) {
            this.showNotification(error.message, 'error');
        }
    },

    async confirmDelete(documentId, filename) {
        if (!confirm(`Tem certeza que deseja excluir o documento "${filename}"?\n\nEsta acao nao pode ser desfeita.`)) {
            return;
        }

        try {
            await this.deleteDocument(documentId);

            // Remover da lista visual
            const item = document.querySelector(`[data-document-id="${documentId}"]`);
            if (item) {
                item.classList.add('fade-out');
                setTimeout(() => item.remove(), 300);
            }

            this.showNotification('Documento excluido com sucesso!', 'success');

            // Atualizar lista se necessario
            if (this.onDocumentDeleted) {
                this.onDocumentDeleted(documentId);
            }

        } catch (error) {
            this.showNotification(error.message, 'error');
        }
    },

    // ============================================================
    // NOTIFICACOES
    // ============================================================

    showNotification(message, type = 'info') {
        // Remover notificacao existente
        const existing = document.querySelector('.doc-notification');
        if (existing) existing.remove();

        const colors = {
            success: 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300',
            error: 'bg-rose-500/20 border-rose-500/50 text-rose-300',
            info: 'bg-blue-500/20 border-blue-500/50 text-blue-300',
            warning: 'bg-amber-500/20 border-amber-500/50 text-amber-300'
        };

        const icons = {
            success: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>',
            error: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>',
            info: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>',
            warning: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>'
        };

        const notification = document.createElement('div');
        notification.className = `doc-notification fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border ${colors[type]} animate-slide-in`;
        notification.innerHTML = `
            <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${icons[type]}
            </svg>
            <span class="text-sm font-medium">${message}</span>
        `;

        document.body.appendChild(notification);

        // Auto-remover apos 4 segundos
        setTimeout(() => {
            notification.classList.add('animate-slide-out');
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    },

    // ============================================================
    // MODAL DE DOCUMENTOS DO CONTRATO
    // ============================================================

    async openContractDocumentsModal(contractId, contractName) {
        // Criar modal se nao existir
        let modal = document.getElementById('contractDocumentsModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'contractDocumentsModal';
            modal.className = 'fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden';
            document.body.appendChild(modal);
        }

        modal.innerHTML = `
            <div class="flex items-center justify-center min-h-screen p-4">
                <div class="bg-dark-900 border border-dark-700 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl">
                    <div class="p-6 border-b border-dark-700 flex items-center justify-between">
                        <div>
                            <h2 class="text-lg font-semibold text-white">Documentos do Contrato</h2>
                            <p class="text-sm text-dark-400 mt-1">${contractName}</p>
                        </div>
                        <button type="button" onclick="DocumentManager.closeDocumentsModal()"
                            class="text-dark-400 hover:text-white transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
                    <div class="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
                        <div id="documentUploadArea" class="mb-6"></div>
                        <div id="documentListArea">
                            <div class="flex items-center justify-center py-8">
                                <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full"></div>
                                <span class="ml-3 text-dark-400">Carregando documentos...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');

        // Fechar ao clicar fora
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeDocumentsModal();
            }
        });

        // Inicializar area de upload
        this.createDropZone('documentUploadArea', contractId, async () => {
            await this.loadAndRenderDocuments(contractId);
        });

        // Carregar documentos existentes
        await this.loadAndRenderDocuments(contractId);

        // Callback para quando documento for excluido
        this.onDocumentDeleted = async () => {
            await this.loadAndRenderDocuments(contractId);
        };
    },

    async loadAndRenderDocuments(contractId) {
        try {
            const data = await this.getContractDocuments(contractId);
            this.createDocumentList('documentListArea', data.documents);
        } catch (error) {
            document.getElementById('documentListArea').innerHTML = `
                <div class="text-center py-8">
                    <p class="text-rose-400 text-sm">${error.message}</p>
                </div>
            `;
        }
    },

    closeDocumentsModal() {
        const modal = document.getElementById('contractDocumentsModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
};

// Expor globalmente
window.DocumentManager = DocumentManager;
