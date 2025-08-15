// Global state
let currentFile = null;
let markdownContent = '';
let epubBlob = null;

// DOM elements
const uploadArea = document.getElementById('upload-area');
const pdfInput = document.getElementById('pdf-input');
const fileInfo = document.getElementById('file-info');
const convertBtn = document.getElementById('convert-btn');
const markdownEditor = document.getElementById('markdown-editor');
const applyPromptBtn = document.getElementById('apply-prompt-btn');
const previewBtn = document.getElementById('preview-btn');
const generateEpubBtn = document.getElementById('generate-epub-btn');
const downloadBtn = document.getElementById('download-btn');
const restartBtn = document.getElementById('restart-btn');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');

// Step sections
const uploadSection = document.getElementById('upload-section');
const editSection = document.getElementById('edit-section');
const downloadSection = document.getElementById('download-section');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
});

function setupEventListeners() {
    // File upload events
    uploadArea.addEventListener('click', () => pdfInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    pdfInput.addEventListener('change', handleFileSelect);
    
    // Button events
    convertBtn.addEventListener('click', convertToMarkdown);
    applyPromptBtn.addEventListener('click', applyCustomTreatment);
    previewBtn.addEventListener('click', previewMarkdown);
    generateEpubBtn.addEventListener('click', generateEpub);
    downloadBtn.addEventListener('click', downloadEpub);
    restartBtn.addEventListener('click', restartProcess);
}

// File handling
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        handleFile(files[0]);
    } else {
        alert('Please drop a PDF file.');
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
        handleFile(file);
    }
}

function handleFile(file) {
    currentFile = file;
    
    // Show file info
    fileInfo.innerHTML = `
        <h4>📄 ${file.name}</h4>
        <p>Size: ${formatFileSize(file.size)}</p>
        <p>Last modified: ${new Date(file.lastModified).toLocaleDateString()}</p>
    `;
    fileInfo.classList.remove('hidden');
    convertBtn.classList.remove('hidden');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// PDF to Markdown conversion
async function convertToMarkdown() {
    if (!currentFile) return;
    
    showLoading('Converting PDF to Markdown...');
    
    try {
        const formData = new FormData();
        formData.append('pdf', currentFile);
        
        const response = await fetch('/api/convert-to-markdown', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        markdownContent = result.markdown;
        markdownEditor.value = markdownContent;
        
        hideLoading();
        showStep('edit');
        
    } catch (error) {
        hideLoading();
        alert('Error converting PDF: ' + error.message);
        console.error('Conversion error:', error);
    }
}

// Custom treatment with prompt
async function applyCustomTreatment() {
    const customPrompt = prompt('Enter your custom treatment prompt:', 
        'Please improve the markdown formatting, fix any OCR errors, and ensure proper academic citation formatting.');
    
    if (!customPrompt) return;
    
    showLoading('Applying custom treatment...');
    
    try {
        const response = await fetch('/api/apply-treatment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                markdown: markdownEditor.value,
                prompt: customPrompt
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        markdownEditor.value = result.treated_markdown;
        
        hideLoading();
        
    } catch (error) {
        hideLoading();
        alert('Error applying treatment: ' + error.message);
        console.error('Treatment error:', error);
    }
}

// Preview markdown
function previewMarkdown() {
    const previewWindow = window.open('', '_blank');
    const markdownHtml = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Markdown Preview</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
                pre { background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; }
                code { background: #f4f4f4; padding: 2px 4px; border-radius: 2px; }
                blockquote { border-left: 4px solid #ddd; margin: 0; padding-left: 20px; color: #666; }
            </style>
        </head>
        <body>
            <pre>${markdownEditor.value}</pre>
        </body>
        </html>
    `;
    previewWindow.document.write(markdownHtml);
    previewWindow.document.close();
}

// Generate EPUB
async function generateEpub() {
    const markdown = markdownEditor.value;
    if (!markdown.trim()) {
        alert('Please add some markdown content first.');
        return;
    }
    
    showLoading('Generating EPUB...');
    
    try {
        const response = await fetch('/api/generate-epub', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                markdown: markdown,
                title: currentFile ? currentFile.name.replace('.pdf', '') : 'Academic Paper'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        epubBlob = await response.blob();
        
        hideLoading();
        showStep('download');
        
    } catch (error) {
        hideLoading();
        alert('Error generating EPUB: ' + error.message);
        console.error('EPUB generation error:', error);
    }
}

// Download EPUB
function downloadEpub() {
    if (!epubBlob) return;
    
    const url = URL.createObjectURL(epubBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (currentFile ? currentFile.name.replace('.pdf', '') : 'academic-paper') + '.epub';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Restart process
function restartProcess() {
    currentFile = null;
    markdownContent = '';
    epubBlob = null;
    markdownEditor.value = '';
    pdfInput.value = '';
    fileInfo.classList.add('hidden');
    convertBtn.classList.add('hidden');
    showStep('upload');
}

// UI helpers
function showStep(step) {
    // Hide all steps
    uploadSection.classList.add('hidden');
    editSection.classList.add('hidden');
    downloadSection.classList.add('hidden');
    
    // Show current step
    switch(step) {
        case 'upload':
            uploadSection.classList.remove('hidden');
            break;
        case 'edit':
            editSection.classList.remove('hidden');
            break;
        case 'download':
            downloadSection.classList.remove('hidden');
            break;
    }
}

function showLoading(message) {
    loadingText.textContent = message;
    loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    loadingOverlay.classList.add('hidden');
}