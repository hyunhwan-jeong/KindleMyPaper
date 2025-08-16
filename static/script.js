// Global state
let currentFile = null;
let fileId = null;
let markdownContent = '';
let epubBlob = null;
let progressTimers = []; // Track progress message timers

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
    initializeAIControls();
});

// Initialize AI controls and set default prompt
async function initializeAIControls() {
    try {
        const customPrompt = document.getElementById('custom-prompt');
        const promptContainer = document.getElementById('prompt-container');
        
        // Set default prompt focused on content preservation
        const defaultPrompt = `CRITICAL: Fix OCR errors and formatting ONLY. Do NOT summarize, shorten, or remove any content.

Rules:
- Preserve EVERY sentence and paragraph exactly
- Only fix obvious OCR mistakes (e.g., "rn" → "m", "cl" → "d")
- Only improve markdown formatting (headers, lists, etc.)
- Keep the exact same content length and detail level
- Do not paraphrase or rewrite anything
- Return the COMPLETE document from start to finish
- Fix LaTeX/equation syntax if needed
- Improve citation formatting if needed

Remember: This is copy-editing, not rewriting. Preserve all academic content exactly.`;
        
        customPrompt.value = defaultPrompt;
        
        // Start with prompt container collapsed
        if (promptContainer) {
            promptContainer.classList.add('collapsed');
            const toggleIcon = document.getElementById('toggle-icon');
            if (toggleIcon) {
                toggleIcon.textContent = '▶';
            }
        }
        
    } catch (error) {
        console.error('Failed to initialize AI controls:', error);
    }
}

// Toggle prompt container visibility
function togglePromptContainer() {
    console.log('🔄 Toggle clicked');
    
    const promptContainer = document.getElementById('prompt-container');
    const toggleIcon = document.getElementById('toggle-icon');
    
    if (!promptContainer || !toggleIcon) {
        console.error('❌ Toggle elements not found');
        return;
    }
    
    if (promptContainer.classList.contains('collapsed')) {
        console.log('📂 Expanding prompt container');
        promptContainer.classList.remove('collapsed');
        toggleIcon.textContent = '▼';
        toggleIcon.style.transform = 'rotate(0deg)';
    } else {
        console.log('📁 Collapsing prompt container');
        promptContainer.classList.add('collapsed');
        toggleIcon.textContent = '▶';
        toggleIcon.style.transform = 'rotate(-90deg)';
    }
}

function setupEventListeners() {
    // File upload events
    uploadArea.addEventListener('click', (e) => {
        // Only trigger if clicking the area itself, not the button
        if (e.target === uploadArea || e.target.closest('.upload-icon') || e.target.tagName === 'P') {
            pdfInput.click();
        }
    });
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    pdfInput.addEventListener('change', handleFileSelect);
    
    // Button events
    convertBtn.addEventListener('click', convertToMarkdown);
    if (applyPromptBtn) {
        applyPromptBtn.addEventListener('click', applyCustomTreatment);
        console.log('✅ AI treatment button listener attached');
    } else {
        console.error('❌ Apply prompt button not found');
    }
    previewBtn.addEventListener('click', previewMarkdown);
    generateEpubBtn.addEventListener('click', generateEpub);
    downloadBtn.addEventListener('click', downloadEpub);
    restartBtn.addEventListener('click', restartProcess);
    
    // AI controls toggle
    const toggleBtn = document.getElementById('toggle-prompt-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', togglePromptContainer);
        console.log('✅ Toggle button listener attached');
    } else {
        console.error('❌ Toggle button not found');
    }
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

async function handleFile(file) {
    currentFile = file;
    
    // Show uploading status
    showLoading('📤 Uploading PDF...');
    
    try {
        // Step 1: Upload the file
        const formData = new FormData();
        formData.append('pdf', file);
        
        const response = await fetch('/api/upload-pdf', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }
        
        const result = await response.json();
        fileId = result.file_id;
        
        // Show file info
        fileInfo.innerHTML = `
            <h4>📄 ${result.filename}</h4>
            <p>Size: ${formatFileSize(result.size)}</p>
            <p>Status: ✅ Uploaded successfully</p>
            <p>File ID: ${fileId}</p>
        `;
        fileInfo.classList.remove('hidden');
        convertBtn.classList.remove('hidden');
        
        hideLoading();
        
    } catch (error) {
        hideLoading();
        alert('Error uploading PDF: ' + error.message);
        console.error('Upload error:', error);
    }
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
    if (!fileId) {
        alert('Please upload a PDF file first.');
        return;
    }
    
    // Show detailed progress
    showLoading('🔄 Starting PDF conversion with marker_single...');
    
    try {
        // Update progress message
        progressTimers.push(setTimeout(() => updateLoadingText('📖 Analyzing PDF layout...'), 2000));
        progressTimers.push(setTimeout(() => updateLoadingText('🔍 Running OCR and text recognition...'), 10000));
        progressTimers.push(setTimeout(() => updateLoadingText('📝 Converting to markdown format...'), 30000));
        
        const response = await fetch(`/api/convert/${fileId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Conversion failed: ${response.status}`);
        }
        
        const result = await response.json();
        markdownContent = result.markdown;
        markdownEditor.value = markdownContent;
        
        // Display extracted images if any
        if (result.images && result.images.length > 0) {
            showExtractedImages(result.images);
        }
        
        updateLoadingText('✅ Conversion complete!');
        setTimeout(() => {
            hideLoading();
            showStep('edit');
        }, 500);
        
    } catch (error) {
        hideLoading();
        alert('Error converting PDF: ' + error.message);
        console.error('Conversion error:', error);
    }
}

function updateLoadingText(message) {
    const loadingText = document.getElementById('loading-text');
    if (loadingText) {
        loadingText.textContent = message;
    }
}

function showExtractedImages(imageUrls) {
    const extractedImagesDiv = document.getElementById('extracted-images');
    const imagesContainer = document.getElementById('images-container');
    
    if (!extractedImagesDiv || !imagesContainer) return;
    
    // Clear previous images
    imagesContainer.innerHTML = '';
    
    if (imageUrls && imageUrls.length > 0) {
        imageUrls.forEach((imageUrl, index) => {
            const imageDiv = document.createElement('div');
            imageDiv.className = 'extracted-image';
            imageDiv.innerHTML = `
                <p><strong>Figure ${index + 1}</strong></p>
                <img src="${imageUrl}" alt="Figure ${index + 1}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px;">
            `;
            imagesContainer.appendChild(imageDiv);
        });
        
        extractedImagesDiv.classList.remove('hidden');
        console.log(`✅ Displayed ${imageUrls.length} extracted images`);
    } else {
        extractedImagesDiv.classList.add('hidden');
    }
}

// AI treatment with enhanced prompt
async function applyCustomTreatment() {
    console.log('🔍 AI treatment started');
    
    const useLLM = true; // Always use AI enhancement
    const customPromptElement = document.getElementById('custom-prompt');
    
    if (!customPromptElement) {
        console.error('❌ Custom prompt element not found');
        return;
    }
    
    // Default enhanced prompt for academic papers with strong content preservation
    const defaultPrompt = `CRITICAL: Fix OCR errors and formatting ONLY. Do NOT summarize, shorten, or remove any content.

Rules:
- Preserve EVERY sentence and paragraph exactly
- Only fix obvious OCR mistakes (e.g., "rn" → "m", "cl" → "d")
- Only improve markdown formatting (headers, lists, etc.)
- Keep the exact same content length and detail level
- Do not paraphrase or rewrite anything
- Return the COMPLETE document from start to finish
- Fix LaTeX/equation syntax if needed
- Improve citation formatting if needed

Remember: This is copy-editing, not rewriting. Preserve all academic content exactly.`;
    
    const customPrompt = customPromptElement.value.trim() || defaultPrompt;
    
    const loadingMessage = '🤖 Applying AI treatment...';
    
    // Disable button during processing
    const btn = document.getElementById('apply-prompt-btn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ Processing...';
    btn.style.backgroundColor = '#6c757d';
    
    showLoading(loadingMessage);
    
    try {
        const response = await fetch('/api/apply-treatment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                markdown: markdownEditor.value,
                prompt: customPrompt,
                use_llm: useLLM
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        markdownEditor.value = result.treated_markdown;
        
        // Update button text to indicate success
        const btn = document.getElementById('apply-prompt-btn');
        const originalText = 'Apply AI Treatment'; // Fixed: use actual original text
        btn.textContent = '✅ Applied Successfully';
        btn.style.backgroundColor = '#28a745';
        btn.disabled = false;
        
        // Show success message
        showTemporaryMessage('✅ AI treatment completed successfully!', 'success');
        
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.backgroundColor = '';
        }, 3000);
        
        hideLoading();
        
    } catch (error) {
        hideLoading();
        
        // Reset button on error
        btn.textContent = 'Apply AI Treatment';
        btn.style.backgroundColor = '';
        btn.disabled = false;
        
        // Show error message
        showTemporaryMessage('❌ Treatment failed: ' + error.message, 'error');
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
    fileId = null;
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
    // Clear any remaining progress timers
    progressTimers.forEach(timer => clearTimeout(timer));
    progressTimers = [];
}

function showTemporaryMessage(message, type = 'info') {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `temp-message temp-message-${type}`;
    messageDiv.textContent = message;
    
    // Style the message
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1001;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        ${type === 'success' ? 'background: #28a745;' : ''}
        ${type === 'error' ? 'background: #dc3545;' : ''}
        ${type === 'info' ? 'background: #17a2b8;' : ''}
    `;
    
    // Add to page
    document.body.appendChild(messageDiv);
    
    // Animate in
    setTimeout(() => {
        messageDiv.style.transform = 'translateX(0)';
        messageDiv.style.opacity = '1';
    }, 100);
    
    // Remove after 4 seconds
    setTimeout(() => {
        messageDiv.style.transform = 'translateX(100%)';
        messageDiv.style.opacity = '0';
        setTimeout(() => {
            if (document.body.contains(messageDiv)) {
                document.body.removeChild(messageDiv);
            }
        }, 300);
    }, 4000);
}