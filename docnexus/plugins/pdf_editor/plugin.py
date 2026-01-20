from flask import Blueprint, jsonify
from docnexus.features.registry import Feature, FeatureType, FeatureState

# Blueprint for future backend operations (saving, merging, etc.)
pdf_bp = Blueprint('pdf_editor', __name__)
blueprint = pdf_bp

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
<div id="pdf-editor-wrapper" style="height: 85vh; width: 100%; display: flex; flex-direction: column; background: var(--bg-secondary); border-radius: 8px; border: 1px solid var(--border-color); overflow: hidden;">
    <!-- Toolbar -->
    <div class="pdf-toolbar" style="padding: 10px; background: var(--bg-primary); border-bottom: 1px solid var(--border-color); display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
        <button class="btn-icon" onclick="PDFEditor.prevPage()"><i class="fas fa-chevron-left"></i></button>
        <span id="pdf-page-num" style="font-family: monospace;">1 / 1</span>
        <button class="btn-icon" onclick="PDFEditor.nextPage()"><i class="fas fa-chevron-right"></i></button>
        <div style="width: 1px; height: 20px; background: var(--border-color); margin: 0 5px;"></div>
        <button class="btn-icon" onclick="PDFEditor.zoomOut()"><i class="fas fa-minus"></i></button>
        <span id="pdf-zoom-level" style="font-size: 0.9rem;">100%</span>
        <button class="btn-icon" onclick="PDFEditor.zoomIn()"><i class="fas fa-plus"></i></button>
        <div style="flex-grow: 1;"></div>
        <!-- Tools (Hidden by default in Read Mode) -->
        <div id="pdf-tools-group" style="display: none; gap: 10px; align-items: center;">
            <div style="width: 1px; height: 20px; background: var(--border-color); margin: 0 5px;"></div>
            <button class="btn-sm" onclick="PDFEditor.setTool('draw')" id="tool-draw"><i class="fas fa-pen"></i> Draw</button>
            <span style="font-size: 0.8rem; color: var(--text-muted); margin-left: 5px;">Editing Mode Active</span>
        </div>
    </div>

    <!-- Canvas Container -->
    <div id="pdf-canvas-container" style="flex-grow: 1; overflow: auto; position: relative; display: flex; justify-content: center; padding: 20px; background: var(--bg-surface);">
        <div id="pdf-page-wrapper" style="position: relative; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
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
    scale: 1.2, // Slightly larger default for better readability
    canvas: null,
    ctx: null,
    drawCanvas: null,
    drawCtx: null,
    
    // Drawing State
    isDrawing: false,
    lastX: 0,
    lastY: 0,
    currentTool: 'none',
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
             // Optional: Debounce
             // this.fitWidth(); 
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
        } else {
            if(toolsGroup) toolsGroup.style.display = 'flex';
            if(drawCanvas) drawCanvas.style.display = 'block';
        }
    },

    load: async function(url) {
        try {
            const loadingTask = pdfjsLib.getDocument(url);
            this.doc = await loadingTask.promise;
            document.getElementById('pdf-page-num').textContent = `${this.pageNum} / ${this.doc.numPages}`;
            
            // Auto Fit Width on Load
            await this.fitWidth();
            
        } catch (e) {
            console.error("PDF Load Error:", e);
            alert("Failed to load PDF: " + e.message);
        }
    },

    fitWidth: async function() {
        if (!this.doc) return;
        const page = await this.doc.getPage(this.pageNum);
        const viewport = page.getViewport({scale: 1.0});
        
        const container = document.getElementById('pdf-canvas-container');
        if (container) {
            // Available width minus current padding (20px * 2)
            const availableWidth = container.clientWidth - 50; 
            if (availableWidth > 0) {
                this.scale = availableWidth / viewport.width;
                // console.log("Auto-fit scale:", this.scale);
            }
        }
        
        this.renderPage(this.pageNum);
        this.updateUI();
    },

    renderPage: async function(num) {
        this.pageRendering = true;
        const page = await this.doc.getPage(num);
        
        const viewport = page.getViewport({scale: this.scale});
        this.canvas.height = viewport.height;
        this.canvas.width = viewport.width;
        
        // Sync Draw Canvas Size
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
        this.renderPage(this.pageNum);
        this.updateUI();
    },

    zoomOut: function() {
        if (this.scale <= 0.5) return;
        this.scale -= 0.25;
        this.renderPage(this.pageNum);
        this.updateUI();
    },

    updateUI: function() {
        document.getElementById('pdf-page-num').textContent = `${this.pageNum} / ${this.doc.numPages}`;
        document.getElementById('pdf-zoom-level').textContent = `${Math.round(this.scale * 100)}%`;
    },
    
    // Tools
    setTool: function(tool) {
        this.currentTool = tool;
        console.log("Tool selected:", tool);
    },
    
    // Drawing Logic
    startDrawing: function(e) {
        if (this.currentTool !== 'draw') return;
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
        
        this.drawCtx.strokeStyle = 'red';
        this.drawCtx.lineWidth = 2;
        this.drawCtx.lineJoin = 'round';
        this.drawCtx.lineCap = 'round';
        
        this.drawCtx.beginPath();
        this.drawCtx.moveTo(this.lastX, this.lastY);
        this.drawCtx.lineTo(x, y);
        this.drawCtx.stroke();
        
        this.lastX = x;
        this.lastY = y;
    },
    
    stopDrawing: function() {
        this.isDrawing = false;
    }
};

// Register System Hook
window.DocNexusPlugins.pdf = {
    onEdit: function() {
        console.log("PDF Editor: Enabling Edit Mode");
        // Just enable tools, no reload needed
        PDFEditor.setReadOnly(false);
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
