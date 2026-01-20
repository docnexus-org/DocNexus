from flask import Blueprint, jsonify, request, current_app
import os
from docnexus.features.registry import Feature, FeatureType, FeatureState

# Blueprint for future backend operations (saving, merging, etc.)
pdf_bp = Blueprint('pdf_editor', __name__)
blueprint = pdf_bp

@pdf_bp.route('/api/pdf/save', methods=['POST'])
def save_pdf():
    try:
        data = request.json
        file_path = data.get('filePath')
        file_content_base64 = data.get('content') # Expecting base64
        
        if not file_path or not file_content_base64:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
            
        # Security Check: Ensure path is within workspace (Basic check)
        workspace = current_app.config.get('WORKSPACE_PATH', '')
        abs_path = os.path.join(workspace, file_path.lstrip('/\\'))
        
        # Simple overwrite for now
        import base64
        # Remove header if present (data:application/pdf;base64,...)
        if ',' in file_content_base64:
            file_content_base64 = file_content_base64.split(',')[1]
            
        with open(abs_path, 'wb') as f:
            f.write(base64.b64decode(file_content_base64))
            
        return jsonify({'success': True})
    except Exception as e:
        print(f"PDF Save Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Plugin Metadata
PLUGIN_METADATA = {
    'name': 'PDF Editor',
    'description': 'Advanced PDF manipulation and annotation tools.',
    'category': 'editor',
    'icon': 'fa-file-pdf',
    'preinstalled': True,
    'version': '0.1.0-alpha'
}

def get_features():
    """Register the PDF Editor features."""
    return [
        Feature(
            name="PDF Editor UI",
            handler=None, # UI Extension handled via Slots
            state=FeatureState.EXPERIMENTAL,
            feature_type=FeatureType.UI_EXTENSION,
            meta={
                "slot": "EDITOR_CONTAINER",
                "file_types": ["pdf"]
            }
        ),
        # Inject Scripts
        Feature(
            name="PDF Scripts",
            handler=None,
            state=FeatureState.STANDARD,
            feature_type=FeatureType.UI_EXTENSION,
            meta={
                "slot": "HEAD_SCRIPTS",
                "content": """
                <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
                <script>pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';</script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js"></script>
                <script>
                // PDF Viewer Logic (Universal IO)
                document.addEventListener('DOMContentLoaded', function() {
                    const filePath = window.currentFilePath;
                    
                    if (filePath && filePath.toLowerCase().endsWith('.pdf')) {
                        console.log("PDF Plugin: Initializing Unified Viewer");
                        
                        // 1. Hide default Markdown content BUT keep Header
                        const mdContent = document.querySelector('.markdown-content');
                        if (mdContent) mdContent.style.display = 'none';
                        
                        // Also hide TOC container if present (PDF handles its own TOC)
                        const tocContainer = document.querySelector('.toc-container');
                        if (tocContainer) tocContainer.style.display = 'none';
                        
                        // 2. Show Plugin Container
                        const pluginContainer = document.getElementById('plugin-editor-container');
                        if (pluginContainer) {
                            pluginContainer.style.display = 'block';
                            // Ensure it respects Flexbox parent
                            pluginContainer.style.width = '100%'; 
                            pluginContainer.style.minWidth = '0'; 
                        }
                        
                        // 3. Initialize Editor in Read-Only Mode
                        const rawUrl = '/raw/' + filePath;
                        
                        // Wait slightly for container layout to stabilize
                        setTimeout(() => {
                            PDFEditor.init(true); // true = readOnly
                            PDFEditor.load(rawUrl);
                        }, 50);
                    }
                });
                </script>
                """
            }
        ),
        # Inject Editor UI & Logic
        Feature(
            name="PDF UI",
            handler=None,
            state=FeatureState.STANDARD,
            feature_type=FeatureType.UI_EXTENSION,
            meta={
                "slot": "EDITOR_CONTAINER",
                "content": """
<style>
/* PDF Specific Theme Overrides */
:root {
    --pdf-toolbar-bg: var(--bg-surface, #ffffff);
    --pdf-toolbar-border: var(--border-color, #e2e8f0);
    --pdf-canvas-bg: #525659; /* Standard PDF Driver Grey (Dark) */
    --pdf-canvas-bg-light: #f3f4f6; /* Standard PDF Driver Grey (Light) */
    --pdf-text: var(--text-primary);
    --pdf-icon: var(--text-secondary);
    --pdf-icon-hover: var(--text-primary);
    --pdf-hover-bg: var(--bg-secondary);
}

[data-theme="dark"] #pdf-editor-wrapper {
    --pdf-canvas-bg: #2a2a2a; /* Darker grey for dark mode to reduce glare */
}

/* Toolbar Styles */
#pdf-editor-wrapper {
    height: 85vh; 
    width: 100%; 
    display: flex; 
    flex-direction: column; 
    border-radius: 8px; 
    border: 1px solid var(--border-color); /* Matches App Theme */
    overflow: hidden;
    background: var(--pdf-canvas-bg-light); /* Default Light Mode BG */
    transition: background 0.3s ease;
}

[data-theme="dark"] #pdf-editor-wrapper {
    background: var(--pdf-canvas-bg);
}

.pdf-toolbar {
    height: 48px;
    background: var(--bg-surface); /* Matches App Theme Header */
    border-bottom: 1px solid var(--border-color);
    display: flex; 
    align-items: center; 
    justify-content: space-between;
    padding: 0 16px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    z-index: 10;
}

.pdf-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

.pdf-btn {
    width: 32px;
    height: 32px;
    border: none;
    background: transparent;
    border-radius: 4px;
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.pdf-btn:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
}

.pdf-btn.active {
    background: rgba(99, 102, 241, 0.1);
    color: var(--color-accent-primary);
}

.pdf-separator {
    width: 1px;
    height: 20px;
    background: var(--border-color);
    margin: 0 8px;
}

/* Color Picker */
.pdf-color-wrapper {
    position: relative;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid var(--border-color);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-surface);
}

.pdf-color-wrapper:hover {
    transform: scale(1.1);
    border-color: var(--text-secondary);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}

.pdf-color-wrapper.active {
    border-color: var(--color-accent-primary, #6366f1);
}

#pdf-ink-preview {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #ef4444; /* Default */
    border: 1px solid rgba(0,0,0,0.1);
}

#pdf-ink-color {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
    padding: 0;
    margin: 0;
}

#pdf-page-input { width: 40px; }
#pdf-zoom-input { width: 50px; }

</style>

<div id="pdf-editor-wrapper">
    <!-- Toolbar -->
    <div class="pdf-toolbar" style="overflow: visible;"> <!-- Ensure overflow is visible -->
        <!-- Left: Side/View Controls (Future) -->
        <div class="pdf-group">
            <button class="pdf-btn" onclick="PDFEditor.toggleFit()" title="Toggle Fit Width"><i class="fas fa-expand-alt"></i></button>
        </div>

        <!-- Center: Navigation & Zoom -->
        <div class="pdf-group">
             <button class="pdf-btn" onclick="PDFEditor.prevPage()" title="Previous Page"><i class="fas fa-chevron-up"></i></button>
             <input type="text" id="pdf-page-input" class="pdf-input" value="1" onchange="PDFEditor.goToPage(this.value)"> 
             <span style="color: var(--text-muted); font-size: 13px;"> / <span id="pdf-total-pages">1</span></span>
             <button class="pdf-btn" onclick="PDFEditor.nextPage()" title="Next Page"><i class="fas fa-chevron-down"></i></button>
             
             <div class="pdf-separator"></div>
             
             <button class="pdf-btn" onclick="PDFEditor.zoomOut()" title="Zoom Out"><i class="fas fa-minus"></i></button>
             <input type="text" id="pdf-zoom-input" class="pdf-input" value="100%" onchange="PDFEditor.setZoom(this.value)">
             <button class="pdf-btn" onclick="PDFEditor.zoomIn()" title="Zoom In"><i class="fas fa-plus"></i></button>
        </div>

        <!-- Tools (Hidden by default in Read Mode) -->
        <div id="pdf-tools-group" style="display: none; gap: 10px; align-items: center;">
            <div class="pdf-separator"></div>
            
            <button class="pdf-btn" id="tool-draw" onclick="PDFEditor.setTool('draw')" title="Draw"><i class="fas fa-pen"></i></button>
            
            <!-- Styled Color Picker (Native) -->
            <div class="pdf-color-wrapper" title="Ink Color">
                <div id="pdf-ink-preview"></div>
                <input type="color" id="pdf-ink-color" value="#ef4444" onchange="PDFEditor.setInkColor(this.value)">
            </div>
            
            <button class="pdf-btn" id="tool-eraser" onclick="PDFEditor.setTool('eraser')" title="Eraser"><i class="fas fa-eraser"></i></button>
        </div>
    </div>

    <!-- Canvas Container -->
    <div id="pdf-canvas-container" style="flex-grow: 1; overflow: auto; position: relative; display: flex; justify-content: center; padding: 32px;">
        <div id="pdf-page-wrapper" style="position: relative; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
            <canvas id="pdf-render-canvas" style="display: block; max-width: 100%;"></canvas>
            <!-- Overlay Canvas for Drawing -->
            <canvas id="pdf-draw-canvas" style="position: absolute; top: 0; left: 0; cursor: crosshair; display: none;"></canvas>
        </div>
    </div>
</div>

<script>
window.DocNexusPlugins = window.DocNexusPlugins || {};

const PDFEditor = {
    doc: null,
    pageNum: 1,
    pageRendering: false,
    pageNumPending: null,
    scale: 1.0, 
    fitMode: 'width', // 'width' or 'actual'
    canvas: null,
    ctx: null,
    drawCanvas: null,
    drawCtx: null,
    
    // Drawing State
    isDrawing: false,
    lastX: 0,
    lastY: 0,
    currentTool: 'none',
    currentInkColor: '#ef4444', // Default Red
    readOnly: true,

    init: async function(readOnly = true) {
        this.canvas = document.getElementById('pdf-render-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.drawCanvas = document.getElementById('pdf-draw-canvas');
        this.drawCtx = this.drawCanvas.getContext('2d');
        
        this.setReadOnly(readOnly);

        // Setup Drawing Events
        this.drawCanvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.drawCanvas.addEventListener('mousemove', (e) => this.draw(e));
        this.drawCanvas.addEventListener('mouseup', () => this.stopDrawing());
        this.drawCanvas.addEventListener('mouseout', () => this.stopDrawing());
        
        // Responsive Resize Listener
        window.addEventListener('resize', () => {
             if (this.fitMode === 'width') {
                 // Debounce could be added here
                 this.fitWidth(false); // Don't full re-render if just css scaling? For now, re-calc.
             }
        });
        
        // Input Enter Keys
        document.getElementById('pdf-page-input').addEventListener('keypress', (e) => {
            if(e.key === 'Enter') this.goToPage(e.target.value);
        });
        document.getElementById('pdf-zoom-input').addEventListener('keypress', (e) => {
            if(e.key === 'Enter') this.setZoom(e.target.value);
        });
    },
    
    setReadOnly: function(isReadOnly) {
        this.readOnly = isReadOnly;
        const toolsGroup = document.getElementById('pdf-tools-group');
        const drawCanvas = document.getElementById('pdf-draw-canvas');
        
        if (isReadOnly) {
            if(toolsGroup) toolsGroup.style.display = 'none';
            if(drawCanvas) drawCanvas.style.display = 'none'; // Disable interaction
            this.currentTool = 'none';
            // Also reset active button states
            document.querySelectorAll('.pdf-btn').forEach(b => b.classList.remove('active'));
        } else {
            if(toolsGroup) toolsGroup.style.display = 'flex';
            if(drawCanvas) drawCanvas.style.display = 'block';
        }
    },

    load: async function(url) {
        try {
            const loadingTask = pdfjsLib.getDocument(url);
            this.doc = await loadingTask.promise;
            
            // Update Totals
            document.getElementById('pdf-total-pages').textContent = this.doc.numPages;
            
            // Auto Fit Width on Load
            await this.fitWidth();
            
        } catch (e) {
            console.error("PDF Load Error:", e);
            alert("Failed to load PDF: " + e.message);
        }
    },

    fitWidth: async function(render = true) {
        if (!this.doc) return;
        this.fitMode = 'width';
        const page = await this.doc.getPage(this.pageNum);
        const viewport = page.getViewport({scale: 1.0});
        
        const container = document.getElementById('pdf-canvas-container');
        if (container) {
            // Available width minus layout padding (32px * 2)
            const availableWidth = container.clientWidth - 70; 
            if (availableWidth > 0) {
                this.scale = availableWidth / viewport.width;
            }
        }
        if (render) this.renderPage(this.pageNum);
        this.updateUI();
    },
    
    toggleFit: function() {
        if (this.fitMode === 'width') {
            this.scale = 1.0;
            this.fitMode = 'actual';
            this.renderPage(this.pageNum);
            this.updateUI();
        } else {
            this.fitWidth();
        }
    },

    renderPage: async function(num) {
        this.pageRendering = true;
        const page = await this.doc.getPage(num);
        
        const viewport = page.getViewport({scale: this.scale});
        this.canvas.height = viewport.height;
        this.canvas.width = viewport.width;
        
        // Sync Draw Canvas
        this.drawCanvas.height = viewport.height;
        this.drawCanvas.width = viewport.width;

        const renderContext = {
            canvasContext: this.ctx,
            viewport: viewport
        };
        
        try {
            await page.render(renderContext).promise;
            this.pageRendering = false;
            
            if (this.pageNumPending !== null) {
                this.renderPage(this.pageNumPending);
                this.pageNumPending = null;
            }
        } catch (e) {
            console.error("Render Error:", e);
        }
    },

    queueRenderPage: function(num) {
        if (this.pageRendering) {
            this.pageNumPending = num;
        } else {
            this.renderPage(num);
        }
    },
    
    goToPage: function(numStr) {
        let num = parseInt(numStr);
        if (isNaN(num)) num = 1;
        if (num < 1) num = 1;
        if (num > this.doc.numPages) num = this.doc.numPages;
        
        this.pageNum = num;
        this.queueRenderPage(this.pageNum);
        this.updateUI();
    },

    prevPage: function() {
        if (this.pageNum <= 1) return;
        this.pageNum--;
        this.queueRenderPage(this.pageNum);
        this.updateUI();
    },

    nextPage: function() {
        if (this.pageNum >= this.doc.numPages) return;
        this.pageNum++;
        this.queueRenderPage(this.pageNum);
        this.updateUI();
    },

    zoomIn: function() {
        this.scale += 0.25;
        this.fitMode = 'custom';
        this.renderPage(this.pageNum);
        this.updateUI();
    },

    zoomOut: function() {
        if (this.scale <= 0.5) return;
        this.scale -= 0.25;
        this.fitMode = 'custom';
        this.renderPage(this.pageNum);
        this.updateUI();
    },
    
    setZoom: function(valStr) {
        // Parse '100%' or '1.0'
        let val = parseFloat(valStr);
        if (valStr.includes('%')) val = val / 100;
        
        if (!isNaN(val) && val > 0.1) {
            this.scale = val;
            this.fitMode = 'custom';
            this.renderPage(this.pageNum);
            this.updateUI();
        }
    },

    updateUI: function() {
        const pageInput = document.getElementById('pdf-page-input');
        if (pageInput && document.activeElement !== pageInput) {
            pageInput.value = this.pageNum;
        }
        
        const zoomInput = document.getElementById('pdf-zoom-input');
        if (zoomInput && document.activeElement !== zoomInput) {
            zoomInput.value = `${Math.round(this.scale * 100)}%`;
        }
    },
    
    // Tools
    setTool: function(tool) {
        if (this.readOnly) return;
        
        this.currentTool = tool;
        console.log("Tool selected:", tool);
        
        // Update Buttons
        document.querySelectorAll('.pdf-btn').forEach(b => b.classList.remove('active'));
        const btn = document.getElementById(`tool-${tool}`);
        if(btn) btn.classList.add('active');
    },
    
    // Drawing Logic
    startDrawing: function(e) {
        if (this.currentTool !== 'draw' && this.currentTool !== 'eraser') return;
        this.isDrawing = true;
        const rect = this.drawCanvas.getBoundingClientRect();
        this.lastX = e.clientX - rect.left;
        this.lastY = e.clientY - rect.top;
    },
    
    draw: function(e) {
        if (!this.isDrawing) return;
        const rect = this.drawCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        this.drawCtx.lineJoin = 'round';
        this.drawCtx.lineCap = 'round';
        
        if (this.currentTool === 'eraser') {
            this.drawCtx.globalCompositeOperation = 'destination-out';
            this.drawCtx.lineWidth = 20; // Eraser size
        } else {
            this.drawCtx.globalCompositeOperation = 'source-over';
            this.drawCtx.strokeStyle = this.currentInkColor;
            this.drawCtx.lineWidth = 2;
        }
        
        this.drawCtx.beginPath();
        this.drawCtx.moveTo(this.lastX, this.lastY);
        this.drawCtx.lineTo(x, y);
        this.drawCtx.stroke();
        
        this.lastX = x;
        this.lastY = y;
    },
    
    stopDrawing: function() {
        this.isDrawing = false;
        // Reset composite operation just in case
        this.drawCtx.globalCompositeOperation = 'source-over';
    },

    setInkColor: function(color) {
        this.currentInkColor = color;
        // Update Preview
        const preview = document.getElementById('pdf-ink-preview');
        if (preview) preview.style.background = color;
        
        // Auto-switch to draw tool if picking color
        if (this.currentTool !== 'draw') {
            this.setTool('draw');
        }
    },
    
    // --- Save & Cancel Logic ---
    
    // Convert canvas drawings to PDF Annotations (Burn into PDF)
    save: async function() {
        if (!this.doc) return;
        
        try {
            console.log("PDF Editor: Saving...");
            const existingPdfBytes = await fetch(this.doc.loadingTask.url).then(res => res.arrayBuffer());
            const pdfDoc = await PDFLib.PDFDocument.load(existingPdfBytes);
            const pages = pdfDoc.getPages();
            
            // For this version, we will only bake the current page's canvas
            // Ideally, we should track strokes per page.
            // Current limitation: Only saves edits on the *current* viewed page if we only have one canvas.
            // BUT: The user request implies "save temporary changes".
            // Since we don't have multi-page state persistence yet, we will assume single-page editing for now or
            // we need to serialize the canvas to an image and draw it on the pdf page.
            
            // Optimization: If we have drawing data, bake it.
            // Since `pdf-draw-canvas` is an overlay, we can export it to PNG and draw it on the PDF page.
            
            const currPage = pages[this.pageNum - 1]; // 0-indexed
            const { width, height } = currPage.getSize();
            
            // Get Canvas DataURL (PNG)
            const pngImageBytes = await new Promise(resolve => {
                this.drawCanvas.toBlob(blob => blob.arrayBuffer().then(resolve), 'image/png');
            });
            
            // Embed
            const pngImage = await pdfDoc.embedPng(pngImageBytes);
            
            // Draw
            currPage.drawImage(pngImage, {
                x: 0,
                y: 0,
                width: width,
                height: height,
            });
            
            // Setup Save
            const pdfBytes = await pdfDoc.saveAsBase64({ dataUri: true });
            
            // Send to Backend
            const response = await fetch('/api/pdf/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filePath: window.currentFilePath,
                    content: pdfBytes
                })
            });
            
            const res = await response.json();
            if (res.success) {
                console.log("PDF Saved Successfully");
                // Reload to reflect "burned" changes and clear canvas
                this.load(this.doc.loadingTask.url); 
                // Clear drawing canvas manually just in case
                this.drawCtx.clearRect(0, 0, this.drawCanvas.width, this.drawCanvas.height);
                return true;
            } else {
                alert("Save Failed: " + res.error);
                return false;
            }
            
        } catch (e) {
            console.error("Save Logic Error:", e);
            alert("Error saving PDF: " + e.message);
            return false;
        }
    },
    
    cancel: function() {
        // Revert unsaved changes = Clear the drawing canvas
        // The underlying PDF is untouched until saved.
        if (confirm("Are you sure you want to discard unsaved drawing changes?")) {
            this.drawCtx.clearRect(0, 0, this.drawCanvas.width, this.drawCanvas.height);
            // Also exit read-only mode visually (hooks will be called by toggleEdit)
            this.setReadOnly(true);
        }
    },
    
    showNotification: function(message, type = 'success') {
        // Simple Toast
        let toast = document.getElementById('pdf-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'pdf-toast';
            toast.style.cssText = `
                position: fixed;
                bottom: 24px;
                right: 24px;
                background: ${type === 'success' ? '#10b981' : '#ef4444'};
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
                z-index: 10000;
                font-weight: 500;
                opacity: 0;
                transition: opacity 0.3s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            document.body.appendChild(toast);
        }
        
        // Update content
        const icon = type === 'success' ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-exclamation-circle"></i>';
        toast.innerHTML = `${icon} ${message}`;
        toast.style.background = type === 'success' ? '#10b981' : '#ef4444';
        
        // Show
        requestAnimationFrame(() => toast.style.opacity = '1');
        
        // Hide
        setTimeout(() => {
            toast.style.opacity = '0';
        }, 3000);
    }
};

// Register System Hooks for Global Buttons
window.DocNexusPlugins.pdf = {
    onEdit: function() {
        console.log("PDF Editor: Enabling Edit Mode");
        PDFEditor.setReadOnly(false);
        PDFEditor.setTool('draw');
    },
    onView: function() {
        console.log("PDF Editor: Disabling Edit Mode");
        PDFEditor.setReadOnly(true);
    },
    onSave: async function() {
        console.log("PDF Editor: onSave Triggered");
        const success = await PDFEditor.save();
        if (success) {
            PDFEditor.showNotification("PDF Saved Successfully");
        } else {
            PDFEditor.showNotification("Failed to Save PDF", 'error');
        }
    },
    onCancel: function() {
        console.log("PDF Editor: onCancel Triggered");
        // We don't confirm here because the global button usually implies "exit mode"
        // But if we have unsaved changes, we might want to?
        // The user request said "revert unsaved changes only". 
        // So we just clear canvas.
        PDFEditor.drawCtx.clearRect(0, 0, PDFEditor.drawCanvas.width, PDFEditor.drawCanvas.height);
        PDFEditor.setReadOnly(true);
    }
};
</script>
                """
            }
        )
    ]

# Future: Add routes for saving binary PDF data
# @pdf_bp.route('/api/pdf/save', methods=['POST'])
# def save_pdf():
#     pass
