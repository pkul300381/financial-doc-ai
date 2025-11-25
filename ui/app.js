// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const API_KEY = ''; // Optional - leave empty for development

// State
let currentDocumentId = null;
let processedDocuments = [];

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const extractionResults = document.getElementById('extractionResults');
const queryInput = document.getElementById('queryInput');
const queryBtn = document.getElementById('queryBtn');
const queryResults = document.getElementById('queryResults');
const documentsList = document.getElementById('documentsList');
const insightsList = document.getElementById('insightsList');
const anomaliesList = document.getElementById('anomaliesList');
const apiStatus = document.getElementById('apiStatus');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    checkAPIStatus();
});

// Event Listeners
function initializeEventListeners() {
    // Upload area
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Query
    queryBtn.addEventListener('click', handleQuery);
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) handleQuery();
    });
}

// API Status Check
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            apiStatus.textContent = 'API Connected';
            apiStatus.parentElement.style.background = 'rgba(16, 185, 129, 0.1)';
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        apiStatus.textContent = 'API Offline';
        apiStatus.parentElement.style.background = 'rgba(239, 68, 68, 0.1)';
        showToast('Cannot connect to API. Make sure the server is running.', 'error');
    }
}

// File Upload Handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

// Upload File
async function uploadFile(file) {
    // Validate file type
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/tiff'];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|png|jpg|jpeg|tiff)$/i)) {
        showToast('Invalid file type. Please upload PDF or image files.', 'error');
        return;
    }
    
    // Show progress
    uploadProgress.classList.remove('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading...';
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('uploader', 'web_ui');
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            progressFill.style.width = `${progress}%`;
        }, 200);
        
        const headers = {};
        if (API_KEY) headers['X-API-Key'] = API_KEY;
        
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
            method: 'POST',
            headers,
            body: formData
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const result = await response.json();
        progressText.textContent = 'Processing complete!';
        
        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            progressFill.style.width = '0%';
        }, 1500);
        
        // Store document
        currentDocumentId = result.document_id;
        processedDocuments.unshift({
            id: result.document_id,
            filename: result.metadata.filename,
            timestamp: new Date(result.metadata.upload_timestamp)
        });
        
        // Update UI
        await loadDocumentDetails(result.document_id);
        updateDocumentsList();
        showToast('Document processed successfully!', 'success');
        
    } catch (error) {
        uploadProgress.classList.add('hidden');
        showToast(`Upload failed: ${error.message}`, 'error');
        console.error('Upload error:', error);
    }
}

// Load Document Details
async function loadDocumentDetails(documentId) {
    try {
        const headers = {};
        if (API_KEY) headers['X-API-Key'] = API_KEY;
        
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
            headers
        });
        
        if (!response.ok) throw new Error('Failed to load document');
        
        const doc = await response.json();
        displayExtractionResults(doc);
        switchTab('extraction');
        
    } catch (error) {
        showToast(`Failed to load document: ${error.message}`, 'error');
    }
}

// Display Extraction Results
function displayExtractionResults(doc) {
    const html = `
        <div class="extraction-grid">
            <div class="info-group">
                <h4>📋 Document Information</h4>
                <div class="info-row">
                    <span class="info-label">Type</span>
                    <span class="info-value">${doc.document_type}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Filename</span>
                    <span class="info-value">${doc.metadata.filename}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Processing Time</span>
                    <span class="info-value">${doc.processing_time_seconds.toFixed(2)}s</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Entities Extracted</span>
                    <span class="info-value">${doc.extracted_entities.length}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Tables Found</span>
                    <span class="info-value">${doc.tables.length}</span>
                </div>
            </div>
            
            ${doc.structured_data ? `
            <div class="info-group">
                <h4>💰 Structured Data</h4>
                ${Object.entries(doc.structured_data).map(([key, value]) => `
                    <div class="info-row">
                        <span class="info-label">${formatKey(key)}</span>
                        <span class="info-value">${formatValue(value)}</span>
                    </div>
                `).join('')}
            </div>
            ` : ''}
            
            ${doc.extracted_entities.length > 0 ? `
            <div class="info-group">
                <h4>🏷️ Extracted Entities</h4>
                ${doc.extracted_entities.slice(0, 10).map(entity => `
                    <div class="info-row">
                        <span class="info-label">${entity.entity_type}</span>
                        <span class="info-value">${entity.value}</span>
                    </div>
                `).join('')}
                ${doc.extracted_entities.length > 10 ? `<p style="margin-top: 1rem; color: var(--text-secondary); font-size: 0.875rem;">... and ${doc.extracted_entities.length - 10} more</p>` : ''}
            </div>
            ` : ''}
            
            ${doc.tables.length > 0 ? `
            <div class="info-group">
                <h4>📊 Tables</h4>
                <p style="color: var(--text-secondary);">Found ${doc.tables.length} table(s) in the document</p>
            </div>
            ` : ''}
            
            <div class="info-group">
                <h4>📝 Raw Text Preview</h4>
                <p style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.6; max-height: 200px; overflow-y: auto;">
                    ${doc.raw_text.substring(0, 500)}${doc.raw_text.length > 500 ? '...' : ''}
                </p>
            </div>
        </div>
    `;
    
    extractionResults.innerHTML = html;
}

// Handle Query
async function handleQuery() {
    const query = queryInput.value.trim();
    if (!query) {
        showToast('Please enter a question', 'warning');
        return;
    }
    
    queryBtn.disabled = true;
    queryBtn.innerHTML = '<span>Processing...</span>';
    queryResults.classList.add('hidden');
    
    try {
        const headers = { 'Content-Type': 'application/json' };
        if (API_KEY) headers['X-API-Key'] = API_KEY;
        
        const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                query,
                document_ids: currentDocumentId ? [currentDocumentId] : null,
                top_k: 5
            })
        });
        
        if (!response.ok) throw new Error('Query failed');
        
        const result = await response.json();
        displayQueryResults(result);
        
    } catch (error) {
        showToast(`Query failed: ${error.message}`, 'error');
    } finally {
        queryBtn.disabled = false;
        queryBtn.innerHTML = `
            <span>Ask Question</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <line x1="22" y1="2" x2="11" y2="13" stroke-width="2"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2" stroke-width="2"/>
            </svg>
        `;
    }
}

// Display Query Results
function displayQueryResults(result) {
    const html = `
        <div class="query-answer">
            <h4>Answer</h4>
            <p>${result.answer}</p>
            <span class="confidence-badge">Confidence: ${(result.confidence * 100).toFixed(0)}%</span>
        </div>
        
        ${result.sources && result.sources.length > 0 ? `
        <div class="sources">
            <h4>Sources</h4>
            ${result.sources.map(source => `
                <div class="source-item">
                    <h5>${source.filename}</h5>
                    <p style="font-size: 0.875rem; color: var(--text-secondary);">${source.excerpt}</p>
                    <span style="font-size: 0.75rem; color: var(--primary);">Relevance: ${(source.relevance_score * 100).toFixed(0)}%</span>
                </div>
            `).join('')}
        </div>
        ` : ''}
    `;
    
    queryResults.innerHTML = html;
    queryResults.classList.remove('hidden');
}

// Update Documents List
function updateDocumentsList() {
    if (processedDocuments.length === 0) {
        documentsList.innerHTML = '<div class="empty-state small"><p>No documents yet</p></div>';
        return;
    }
    
    const html = processedDocuments.map(doc => `
        <div class="document-item" onclick="loadDocumentDetails('${doc.id}')">
            <h4>${doc.filename}</h4>
            <div class="document-meta">
                ${new Date(doc.timestamp).toLocaleString()}
            </div>
        </div>
    `).join('');
    
    documentsList.innerHTML = html;
}

// Tab Switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `${tabName}-tab`);
    });
    
    // Load data for insights/anomalies tab
    if (tabName === 'insights' && processedDocuments.length > 0) {
        loadInsightsAndAnomalies();
    }
}

// Load Insights and Anomalies
async function loadInsightsAndAnomalies() {
    try {
        const headers = {};
        if (API_KEY) headers['X-API-Key'] = API_KEY;
        
        // Load insights
        const insightsResponse = await fetch(`${API_BASE_URL}/api/v1/insights`, { headers });
        if (insightsResponse.ok) {
            const insights = await insightsResponse.json();
            displayInsights(insights);
        }
        
        // Load anomalies
        const anomaliesResponse = await fetch(`${API_BASE_URL}/api/v1/anomalies`, { headers });
        if (anomaliesResponse.ok) {
            const anomalies = await anomaliesResponse.json();
            displayAnomalies(anomalies);
        }
        
    } catch (error) {
        console.error('Failed to load insights/anomalies:', error);
    }
}

// Display Insights
function displayInsights(insights) {
    if (!insights || insights.length === 0) {
        insightsList.innerHTML = '<div class="empty-state"><p>No insights available yet</p></div>';
        return;
    }
    
    const html = insights.map(insight => `
        <div class="info-group">
            <h4>${insight.title}</h4>
            <p style="color: var(--text-secondary); margin-bottom: 0.5rem;">${insight.description}</p>
            <span class="confidence-badge">Confidence: ${(insight.confidence * 100).toFixed(0)}%</span>
        </div>
    `).join('');
    
    insightsList.innerHTML = html;
}

// Display Anomalies
function displayAnomalies(anomalies) {
    if (!anomalies || anomalies.length === 0) {
        anomaliesList.innerHTML = '<div class="empty-state"><p>No anomalies detected</p></div>';
        return;
    }
    
    const html = anomalies.map(anomaly => `
        <div class="info-group" style="border-left: 3px solid var(--danger);">
            <h4>⚠️ ${anomaly.anomaly_type}</h4>
            <p style="color: var(--text-secondary); margin-bottom: 0.5rem;">${anomaly.description}</p>
            <div class="info-row">
                <span class="info-label">Severity</span>
                <span class="info-value" style="color: var(--danger);">${anomaly.severity}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Confidence</span>
                <span class="info-value">${(anomaly.confidence_score * 100).toFixed(0)}%</span>
            </div>
        </div>
    `).join('');
    
    anomaliesList.innerHTML = html;
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    const container = document.getElementById('toastContainer');
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility Functions
function formatKey(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatValue(value) {
    if (typeof value === 'object' && value !== null) {
        if (value.amount !== undefined) {
            return `${value.currency || ''} ${value.amount}`;
        }
        return JSON.stringify(value);
    }
    return value;
}
