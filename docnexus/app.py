"""
Markdown Documentation Viewer
A Flask-based web application that presents Markdown files from a folder as well-formatted HTML sections.
"""

from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for, abort, Response, session, send_file
import os
import sys
import markdown
from pathlib import Path
from datetime import datetime
import io
import re
import html as html_module
import json
import shutil
import logging
from logging.handlers import RotatingFileHandler
import zipfile
import urllib.request
import subprocess
import tempfile
from bs4 import BeautifulSoup

# Legacy imports removed (pdfkit, htmldocx, mammoth) as part of Plugin Architecture Refactor

try:
    from docnexus.core.renderer import render_baseline, run_pipeline
    from docnexus.features.registry import FeatureManager, Feature, FeatureState
    from docnexus.features import smart_convert as smart
    from docnexus.features.standard import normalize_headings, sanitize_attr_tokens, build_toc, annotate_blocks
except Exception:
    # allow running as a script: add project root to sys.path, then absolute imports
    PROJECT_ROOT_FOR_PATH = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT_FOR_PATH) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT_FOR_PATH))
    from docnexus.core.renderer import render_baseline, run_pipeline
    from docnexus.features.registry import FeatureManager, Feature, FeatureState
    from docnexus.features import smart_convert as smart
    from docnexus.features import smart_convert as smart
    from docnexus.features.standard import normalize_headings, sanitize_attr_tokens, build_toc, annotate_blocks

from docnexus.core.loader import load_plugins
from docnexus.features.registry import PluginRegistry

# Input Support Configuration
try:
    import mammoth
    WORD_INPUT_AVAILABLE = True
    def convert_docx_to_html(start_path):
        with open(start_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            return result.value
except ImportError:
    WORD_INPUT_AVAILABLE = False
    def convert_docx_to_html(start_path):
        raise ImportError("mammoth library not installed")

import os

# Standard Version Loading (Fail Fast)
# In production/rendering, we rely on this import succeeding.
# If it fails, the application cannot ensure data integrity regarding its version.
from docnexus.version_info import __version__ as VERSION

# Configuration
flask_kwargs = {'static_folder': 'static'}

# Detect Environment
if getattr(sys, 'frozen', False):
    # Running as compiled executable (PyInstaller)
    # sys._MEIPASS is the temp folder where PyInstaller extracts bundled files
    BUNDLE_DIR = Path(sys._MEIPASS).resolve()
    PROJECT_ROOT = Path(sys.executable).parent
    
    # Bundle structure: sys._MEIPASS/docnexus/templates
    flask_kwargs['template_folder'] = str(BUNDLE_DIR / 'docnexus' / 'templates')
    flask_kwargs['static_folder'] = str(BUNDLE_DIR / 'docnexus' / 'static')
else:
    # Running from source
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Create Flask App (SINGLE INSTANCE)
app = Flask(__name__, **flask_kwargs)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'dev-key-123'

# Disable Caching for Development/Updates
@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    # Content Security Policy (Liberal for local app with heavy JS libs like Mermaid/KaTeX)
    r.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: "
        "https://fonts.googleapis.com https://fonts.gstatic.com "
        "https://cdnjs.cloudflare.com https://cdn.jsdelivr.net "
        "https://uicdn.toast.com;"
    )
    return r

# Global Feature Manager (initialized later)
FEATURES = None

# Global Template Context
@app.context_processor
def inject_global_context():
    # Use global registry instance if possible, or new one (singleton handles it)
    reg = PluginRegistry()
    # Debug logging for this context injection
    # logger is not initialized yet here, so we use print or wait
    return {
        'version': VERSION,
        'get_slots': reg.get_slots
    }

@app.route('/api/version')
def get_version():
    return jsonify({'version': VERSION})

@app.route('/api/plugins')
def get_plugins():
    """
    Return list of available plugins using Metadata and Config state.
    """
    from docnexus.core.loader import get_plugin_paths
    from docnexus.core.state import PluginState
    import ast
    
    logger.debug("API: Fetching plugin list (New Architecture)...")
    plugins = []
    seen_ids = set()
    
    # Load State
    state = PluginState.get_instance()
    installed_ids = state.get_installed_plugins()
    
    paths = get_plugin_paths()
    for base_path in paths:
        if not base_path.exists():
            continue
            
        is_bundled = 'docnexus' in str(base_path).lower() and ('plugins' in base_path.name or 'plugins_dev' in base_path.name)
        origin_label = 'bundled' if is_bundled else 'user'
        
        for item in base_path.iterdir():
            if item.is_dir() and (item / 'plugin.py').exists():
                plugin_id = item.name
                if plugin_id in seen_ids:
                    continue
                seen_ids.add(plugin_id)
                
                # Default Metadata
                display_name = plugin_id.title()
                desc = "No description."
                category = "tool"
                icon = "fa-plug"
                preinstalled = False
                
                # Robust Regex Metadata Extraction
                try:
                    import re
                    import ast
                    
                    plugin_file_path = item / 'plugin.py'
                    with open(plugin_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Regex to find PLUGIN_METADATA = { ... }
                    # Matches keys and values broadly, expecting valid python dict syntax
                    match = re.search(r'PLUGIN_METADATA\s*=\s*({[^}]+})', content, re.DOTALL)
                    
                    if match:
                        dict_str = match.group(1)
                        # clean up any potential trailing commas or comments if simple regex captured them?
                        # actually ast.literal_eval is strict.
                        # If regex is too greedy, it might fail.
                        # Let's try to parse the match.
                        meta = ast.literal_eval(dict_str)
                        
                        display_name = meta.get('name', display_name)
                        desc = meta.get('description', desc)
                        category = meta.get('category', category)
                        icon = meta.get('icon', icon)
                        preinstalled = meta.get('preinstalled', False)
                    else:
                        logger.warning(f"No PLUGIN_METADATA found in {plugin_id}")
                        
                except Exception as e:
                    logger.warning(f"Failed to regex-parse metadata for {plugin_id}: {e}")
                
                # Determine Installed Status
                if preinstalled:
                     is_installed = True
                     has_installer = False # Preinstalled cannot be removed
                else:
                    is_installed = plugin_id in installed_ids
                    has_installer = True # Can be managed

                if plugin_id == 'pdf_export':
                     logger.info(f"API: get_plugins found pdf_export. State says installed={is_installed} (Instance {id(state)})")
                # Priority (Config read)
                priority_list = CONFIG.get('plugin_priority', [])
                is_priority = plugin_id in priority_list

                plugins.append({
                    'id': plugin_id,
                    'name': display_name,
                    'author': 'DocNexus Core' if is_bundled else 'User',
                    'downloads': '-',
                    'category': category,
                    'tags': [origin_label, category],
                    'description': desc,
                    'icon': icon,
                    'installed': is_installed,
                    'can_install': has_installer,
                    'type': origin_label,
                    'is_priority': is_priority
                })
                
    return jsonify(plugins)

@app.route('/api/plugins/install/<plugin_id>', methods=['POST'])
def install_plugin_api(plugin_id):
    logger.info(f"API: Received install request for {plugin_id}")
    from docnexus.core.state import PluginState
    state = PluginState.get_instance()
    
    # 1. Update State
    try:
        if state.set_plugin_installed(plugin_id, True):
            logger.info(f"API: Successfully enabled {plugin_id}")
            
            # 2. Reload Plugin & Refresh Features
            try:
                from docnexus.core.loader import load_single_plugin, get_plugin_paths
                from docnexus.features.registry import PluginRegistry
                
                # Retrieve path for this plugin
                # We need to find where it is.
                found_path = None
                for base in get_plugin_paths():
                    candidate = base / plugin_id / 'plugin.py'
                    if candidate.exists():
                        found_path = candidate
                        break
                
                if found_path:
                    load_single_plugin(plugin_id, found_path, PluginRegistry())
                    FEATURES.refresh()
                    logger.info(f"API: Reloaded plugin {plugin_id} and refreshed features.")
                else:
                    logger.warning(f"API: Could not find path for {plugin_id} to reload.")
                    
            except Exception as reload_err:
                logger.error(f"API: Reload failed: {reload_err}")
                
            return jsonify({'message': f'Plugin {plugin_id} enabled successfully.'})
        else:
            logger.error(f"API: Failed to save configuration for {plugin_id}")
            return jsonify({'error': 'Failed to save configuration.'}), 500
    except Exception as e:
        logger.error(f"API: Exception during install of {plugin_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/plugins/uninstall/<plugin_id>', methods=['POST'])
def uninstall_plugin_api(plugin_id):
    logger.info(f"API: Received uninstall request for {plugin_id}")
    from docnexus.core.state import PluginState
    state = PluginState.get_instance()
    
    # 1. Update State
    try:
        if state.set_plugin_installed(plugin_id, False):
            logger.info(f"API: Successfully disabled {plugin_id}")
            
            # 2. Refresh Features (Refresh will see State=False and disable feature)
            try:
                FEATURES.refresh()
                logger.info(f"API: Refreshed features (Plugin {plugin_id} should be disabled).")
            except Exception as ref_err:
                logger.error(f"API: Refresh failed: {ref_err}")
                
            return jsonify({'message': f'Plugin {plugin_id} disabled successfully.'})
        else:
            logger.error(f"API: Failed to save configuration for {plugin_id}")
            return jsonify({'error': 'Failed to save configuration.'}), 500
    except Exception as e:
        logger.error(f"API: Exception during uninstall of {plugin_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/plugins/priority', methods=['GET', 'POST'])
def manage_priority():
    """Get or Set plugin priority list."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            priority_list = data.get('priority', [])
            if not isinstance(priority_list, list):
                return jsonify({'error': 'Invalid format, expected list'}), 400
            
            CONFIG['plugin_priority'] = priority_list
            save_config(CONFIG)
            
            # Refresh features to apply new priority
            FEATURES.refresh(priority_list=priority_list)
            
            return jsonify({'success': True, 'priority': priority_list})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'priority': CONFIG.get('plugin_priority', [])})


# Note: We do NOT set MAX_CONTENT_LENGTH here because:
# 1. Form-encoded data can be 2-3x larger than actual file content
# 2. We validate actual file/content size at the application level instead
# 3. This allows the server to accept the HTTP request and check the actual data size intelligently

import webbrowser
import logging
from threading import Timer
from pathlib import Path
from docnexus.core.logging_config import setup_logging

# Initialize Logging (Standardized)
# Initialize Logging (Standardized)
DEBUG_MODE = os.environ.get('FLASK_ENV') == 'development'

if getattr(sys, 'frozen', False):
    # If frozen, use the directory of the executable for persistent logs
    BASE_DIR = Path(sys.executable).parent
else:
    # If running from source, use the project root
    BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = BASE_DIR / 'logs'
setup_logging(LOG_DIR, DEBUG_MODE)

logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)
logger.info(f"Application starting - Version {VERSION} | Debug Mode: {DEBUG_MODE}")

# Initialize Plugins
try:
    import time
    logger.info(f"Initializing Plugin System... (Startup Time: {time.time()})")
    
    # Force loader logging to ensure we see plugin discovery
    logging.getLogger('docnexus.core.loader').setLevel(logging.DEBUG)
    
    # Initialize Registry
    registry = PluginRegistry()
    logger.info(f"App sees PluginRegistry ID: {id(registry)}")
    
    # Load Plugins
    from docnexus.core.loader import load_plugins
    load_plugins(registry)
    logger.info(f"App sees PluginRegistry ID: {id(registry)}")
    registry.initialize_all()
    
    if hasattr(registry, 'register_blueprints'):
        registry.register_blueprints(app)
        
        # Fallback: Explicitly register editor if missing (fixes loader discovery issues)
        try:
            from docnexus.plugins.editor.plugin import blueprint as editor_bp
            if 'editor' not in [bp.name for bp in app.blueprints.values()]:
                app.register_blueprint(editor_bp)
                logger.info("Registered editor blueprint (fallback)")
            else:
                 logger.info("Editor blueprint already registered via registry.")
        except Exception as e:
            logger.warning(f"Fallback registration skipped: {e}")
            
    else:
        logger.error("Registry missing register_blueprints method!")
    
    # Initialize FeatureManager and load plugins we just found
    # global FEATURES  <-- Removed
    try:
        from docnexus.features.registry import FeatureManager
        if FEATURES is None:
            FEATURES = FeatureManager(registry)
        
        logger.info("Refreshing global FEATURES manager...")
        FEATURES.refresh()
    except Exception as fm_err:
        logger.error(f"Failed to initialize FeatureManager: {fm_err}", exc_info=True)

    logger.info(f"Registry initialized. Plugin count: {len(registry.get_all_plugins())}")
    logger.debug(f"Registry contents: {registry.get_all_plugins()}")
    
    # DEBUG: Verify Registry Health
    if hasattr(registry, 'get_slots'):
        logger.info("Registry Health Check: get_slots() available")
    else:
        logger.error("Registry Health Check: get_slots() MISSING!")
        
except Exception as e:
    logger.error(f"Plugin system initialization failed: {e}", exc_info=True)

@app.errorhandler(500)
def internal_error(error):
    import traceback
    logger.error(f"500 Error: {error}\n{traceback.format_exc()}")
    return f"Internal Server Error: {error}<br><pre>{traceback.format_exc()}</pre>", 500

# Workspace Configuration
CONFIG_FILE = PROJECT_ROOT / 'config.json'

def load_config():
    """Load workspace configuration."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    # Determine default workspace
    default_workspace = PROJECT_ROOT / 'workspace'
    if not default_workspace.exists() and (PROJECT_ROOT / 'examples').exists():
        default_workspace = PROJECT_ROOT / 'examples'

    return {
        'workspaces': [str(default_workspace)],
        'active_workspace': str(default_workspace),
        'recent_workspaces': []
    }

def save_config(config):
    """Save workspace configuration."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

# Load configuration
CONFIG = load_config()
MD_FOLDER = Path(CONFIG['active_workspace'])  # Folder containing documents
DOCS_FOLDER = PROJECT_ROOT / 'docs'  # Documentation folder
ALLOWED_EXTENSIONS = {'.md', '.markdown', '.txt', '.docx', '.pdf'}

# File size limits (in bytes)
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB for actual file content
MAX_EXPORT_HTML_SIZE = 50 * 1024 * 1024  # 50 MB for export HTML content

# Feature registry: keep smart/experimental separate from baseline rendering
FEATURES = FeatureManager()
# STANDARD features (always run)
FEATURES.register(Feature("STD_NORMALIZE", normalize_headings, FeatureState.STANDARD))
FEATURES.register(Feature("STD_SANITIZE_ATTR", sanitize_attr_tokens, FeatureState.STANDARD))
FEATURES.register(Feature("STD_TOC", build_toc, FeatureState.STANDARD))
FEATURES.register(Feature("STD_ANNOTATE", annotate_blocks, FeatureState.STANDARD))
# EXPERIMENTAL features (smart toggle) - Registered but disabled in v1.0.0
# Will be re-enabled in v1.1/1.2 with proper UI - see doc/FUTURE_FEATURES.md
FEATURES.register(Feature("SMART_TABLES", smart.convert_ascii_tables_to_markdown, FeatureState.EXPERIMENTAL))
FEATURES.register(Feature("SMART_SIP", smart.convert_sip_signaling_to_mermaid, FeatureState.EXPERIMENTAL))
FEATURES.register(Feature("SMART_TOPOLOGY", smart.convert_topology_to_mermaid, FeatureState.EXPERIMENTAL))

# Connect FeatureManager to Registry (Facade Pattern)
# This allows FeatureManager to pull "Algorithm" features from plugins
FEATURES._registry = PluginRegistry()
# Force debug print to console
logger.debug(f"DEBUG_STARTUP: Plugins in Registry: {FEATURES._registry.get_all_plugins()}")
FEATURES.refresh(priority_list=CONFIG.get('plugin_priority', []))
logger.debug(f"DEBUG_STARTUP: Features in Manager: {[f.name for f in FEATURES._features]}")


# Context Processor for Debugging (moved here after all config is loaded)
@app.context_processor
def inject_debug_info():
    try:
        # Resolve template folder to absolute path
        template_path = Path(app.template_folder)
        if not template_path.is_absolute():
            template_path = Path(app.root_path) / template_path
        
        return {
            'debug_info': {
                'project_root': str(PROJECT_ROOT),
                'md_folder': str(MD_FOLDER),
                'template_folder': str(template_path),
                'frozen': getattr(sys, 'frozen', False),
                'python_path': str(sys.executable),
                'version': VERSION
            }
        }
    except Exception as e:
        logger.error(f"Error in context processor: {e}")
        return {'debug_info': {'error': str(e)}}

# SIP Protocol Knowledge Base
SIP_KNOWLEDGE = {
    'request_methods': [
        'INVITE', 'ACK', 'BYE', 'CANCEL', 'REGISTER', 'OPTIONS',
        'PRACK', 'SUBSCRIBE', 'NOTIFY', 'PUBLISH', 'INFO', 'REFER',
        'MESSAGE', 'UPDATE'
    ],
    'response_codes': {
        # 1xx Provisional
        '100': 'Trying', '180': 'Ringing', '181': 'Call Is Being Forwarded',
        '182': 'Queued', '183': 'Session Progress',
        # 2xx Success
        '200': 'OK', '202': 'Accepted',
        # 3xx Redirection
        '300': 'Multiple Choices', '301': 'Moved Permanently', '302': 'Moved Temporarily',
        # 4xx Client Error
        '400': 'Bad Request', '401': 'Unauthorized', '403': 'Forbidden',
        '404': 'Not Found', '408': 'Request Timeout', '486': 'Busy Here',
        '487': 'Request Terminated',
        # 5xx Server Error
        '500': 'Server Internal Error', '503': 'Service Unavailable',
        # 6xx Global Failure
        '600': 'Busy Everywhere', '603': 'Decline', '604': 'Does Not Exist Anywhere'
    },
    'call_flow_patterns': {
        'basic_call': ['INVITE', '100 Trying', '180 Ringing', '200 OK', 'ACK', 'BYE', '200 OK'],
        'with_prack': ['INVITE', '100 Trying', '183 Session Progress', 'PRACK', '200 OK', '180 Ringing', 'PRACK', '200 OK', '200 OK', 'ACK'],
        'cancel': ['INVITE', '100 Trying', 'CANCEL', '200 OK', '487 Request Terminated', 'ACK'],
        'busy': ['INVITE', '100 Trying', '486 Busy Here', 'ACK'],
        'declined': ['INVITE', '100 Trying', '603 Decline', 'ACK']
    },
    'headers': [
        'Via', 'From', 'To', 'Call-ID', 'CSeq', 'Contact', 'Max-Forwards',
        'Content-Type', 'Content-Length', 'User-Agent', 'Allow', 'Supported'
    ],
    'sdp_attributes': ['RTP', 'SRTP', 'RTCP', 'codec', 'sendrecv', 'recvonly', 'sendonly']
}

def get_markdown_files(subdir=None, recursive=True):
    """
    Get markdown files and subdirectories.
    If recursive=True, returns flat list of all files (legacy behavior).
    If recursive=False, returns list of files and directories in subdir.
    """
    md_path = Path(MD_FOLDER)
    if subdir:
        md_path = md_path / subdir
        # Security check: ensure we haven't traversed out of MD_FOLDER
        try:
            md_path.resolve().relative_to(Path(MD_FOLDER).resolve())
        except ValueError:
            logger.warning(f"Attempted path traversal: {subdir}")
            return []
    if not md_path.exists():
        if not subdir: # Only create root if missing
            md_path.mkdir(parents=True, exist_ok=True)
        return []
    
    items = []
    
    if recursive:
        # Legacy/Search Behavior: Recursive flat list of files
        iterator = md_path.rglob('*')
    else:
        # Explorer Behavior: Direct children only
        iterator = md_path.iterdir()

    for file_path in iterator:
        rel_path_obj = file_path.relative_to(Path(MD_FOLDER)) 
        rel_path = str(rel_path_obj).replace('\\', '/')
        
        # Handle Directories (Only in non-recursive mode)
        if not recursive and file_path.is_dir():
            # Skip hidden folders
            if file_path.name.startswith('.'): continue
            
            items.append({
                'name': file_path.name,
                'filename': file_path.name,
                'relative_path': rel_path, # e.g. "subfolder"
                'folder': str(Path(subdir) if subdir else ''),
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'size': f"{len(list(file_path.iterdir()))} items",
                'type': 'dir'
            })
            continue

        # Handle Files
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            stat = file_path.stat()
            # Folder is the parent relative to MD_FOLDER
            folder = str(rel_path_obj.parent).replace('\\', '/')
            if folder == '.': folder = ''
            
            # Format size
            size_bytes = stat.st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                
            items.append({
                'name': file_path.stem,
                'filename': file_path.name,
                'relative_path': rel_path,
                'folder': folder,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'size': size_str,
                'type': file_path.suffix.lower().strip('.')
            })
    
    # Sort items: Directories first, then files
    items.sort(key=lambda x: (x['type'] != 'dir', x['name'].lower()))
    return items

def convert_ascii_tables_to_markdown(content):
    """Convert ASCII tables, network topology, and SIP flow diagrams to appropriate formats."""
    import re
    
    def get_preceding_heading(content, code_block_start):
        """Get the heading that precedes a code block."""
        lines_before = content[:code_block_start].split('\n')
        # Look backwards for the nearest heading
        for line in reversed(lines_before[-10:]):  # Check last 10 lines
            if line.startswith('#'):
                return line.strip()
        return ''
    
    def should_convert_topology(heading):
        """Check if heading suggests this should be a topology diagram."""
        topology_keywords = ['topology', 'network', 'architecture', 'setup', 'configuration']
        heading_lower = heading.lower()
        return any(keyword in heading_lower for keyword in topology_keywords)
    
    def should_convert_signaling(heading):
        """Check if heading suggests this should be a signaling/flow diagram."""
        flow_keywords = ['flow', 'signaling', 'sequence', 'call flow', 'message flow', 'sip']
        heading_lower = heading.lower()
        return any(keyword in heading_lower for keyword in flow_keywords)
    
    def detect_network_topology(lines):
        """Detect if this is a network topology diagram."""
        text = '\n'.join(lines)
        # Check for topology indicators
        topology_indicators = ['UAC', 'UAS', 'Router', 'Server', 'Switch', 'Gateway', 'Proxy']
        box_chars = ['┌', '─', '┐', '│', '└', '┘', '├', '┤', '┬', '┴']
        
        has_boxes = sum(1 for char in box_chars if char in text) >= 5
        has_topology_terms = sum(1 for term in topology_indicators if term in text) >= 2
        has_ip_addresses = bool(re.search(r'\d+\.\d+\.\d+\.\d+', text))
        
        # Must have boxes AND either topology terms or IP addresses
        return has_boxes and (has_topology_terms or has_ip_addresses)
    
    def detect_sip_signaling(lines):
        """Detect if this is a SIP signaling flow diagram using SIP knowledge."""
        text = '\n'.join(lines)
        text_upper = text.upper()
        
        # Check for SIP request methods
        request_count = sum(1 for method in SIP_KNOWLEDGE['request_methods'] if method in text_upper)
        
        # Check for SIP response codes
        response_count = 0
        for code, desc in SIP_KNOWLEDGE['response_codes'].items():
            if f'{code} {desc}' in text or code in text or desc.upper() in text_upper:
                response_count += 1
        
        # Flow indicators
        has_arrows = any(arrow in text for arrow in ['──>', '<──', '→', '←', '────>', '<────'])
        has_timing = 'T+' in text or 'TIME' in lines[0] if lines else False
        has_process_notes = any(char in text for char in ['┌', '├', '└'])
        
        # Strong indicators: arrows + (timing OR process notes) + (requests OR responses)
        return has_arrows and (has_timing or has_process_notes) and (request_count >= 2 or response_count >= 2)
    
    def convert_topology_to_mermaid(lines):
        """Convert network topology to Mermaid flowchart."""
        text = '\n'.join(lines)
        
        # Extract network elements
        patterns = [
            r'(UAC|UAS)\s*\(([^)]+)\)',
            r'(Crestone Router|Router|Server|Gateway|Proxy)\s*(\d+)?\s*\(([^)]+)\)',
            r'(Crestone Router \d+)',
        ]
        
        nodes = []
        node_details = {}
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0)
                # Extract name and details
                if '(' in full_match:
                    name_part = full_match.split('(')[0].strip()
                    detail_part = full_match.split('(')[1].split(')')[0].strip()
                    if name_part not in nodes:
                        nodes.append(name_part)
                        node_details[name_part] = detail_part
                else:
                    if full_match not in nodes and len(full_match) < 50:
                        nodes.append(full_match)
        
        # If we found nodes, create a flowchart
        if len(nodes) >= 2:
            mermaid_lines = ['```mermaid', 'flowchart LR']
            
            # Create nodes with details
            for i, node in enumerate(nodes):
                node_id = f'N{i}'
                if node in node_details:
                    label = f"{node}<br/>{node_details[node]}"
                else:
                    label = node
                mermaid_lines.append(f'    {node_id}["{label}"]')
            
            # Create connections (left-to-right flow)
            for i in range(len(nodes) - 1):
                mermaid_lines.append(f'    N{i} -->|TCP/RTP| N{i+1}')
            
            # Style
            mermaid_lines.append('    classDef default fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000')
            mermaid_lines.append('```')
            
            return '\n'.join(mermaid_lines)
        
        return None
    
    def convert_sip_signaling_to_mermaid(lines):
        """Convert SIP signaling flow to Mermaid sequence diagram using SIP knowledge."""
        # Extract participants from header
        participants = []
        
        # Find the line with participant names
        for i, line in enumerate(lines[:5]):
            if not line.strip().startswith('-') and 'Time' not in line:
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) >= 3:
                    participants = [p.strip() for p in parts if p.strip() and not p.startswith('T+')]
                    break
        
        # Clean participant names (remove IP addresses)
        clean_participants = []
        for p in participants:
            clean_p = re.sub(r'\s*\([^)]*\)', '', p).strip()
            if clean_p and clean_p.lower() not in ['time']:
                clean_participants.append(clean_p)
        
        participants = clean_participants[:5]
        
        if len(participants) < 2:
            participants = ['UAC', 'Router1', 'Router2', 'UAS']
        
        # Build Mermaid sequence diagram
        mermaid_lines = ['```mermaid', 'sequenceDiagram']
        
        # Add participants
        for p in participants:
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', p)
            mermaid_lines.append(f'    participant {safe_name} as {p}')
        
        # Parse message flows using SIP knowledge
        current_time = None
        for line in lines[2:]:  # Skip header lines
            if line.strip().startswith('---'):
                continue
            
            # Extract timing
            time_match = re.match(r'(T\+\d+\w+)', line)
            if time_match:
                current_time = time_match.group(1)
            
            # Right arrow messages
            if '──>' in line or '───>' in line or '────>' in line or '→' in line:
                message = 'Message'
                
                # Check SIP request methods
                for method in SIP_KNOWLEDGE['request_methods']:
                    if method in line.upper():
                        message = method
                        if current_time:
                            message = f'{method} [{current_time}]'
                        break
                
                # Check SIP response codes
                if message == 'Message':
                    for code, desc in SIP_KNOWLEDGE['response_codes'].items():
                        if f'{code} {desc}' in line or f'{code}' in line[:10]:
                            message = f'{code} {desc}'
                            if current_time:
                                message = f'{code} {desc} [{current_time}]'
                            break
                
                # Extract additional info from line (RTP, SRTP, etc.)
                for attr in SIP_KNOWLEDGE['sdp_attributes']:
                    if attr in line and attr not in message:
                        message = f'{message} ({attr})'
                        break
                
                if len(participants) >= 2:
                    for i in range(len(participants) - 1):
                        src = re.sub(r'[^a-zA-Z0-9_]', '_', participants[i])
                        dst = re.sub(r'[^a-zA-Z0-9_]', '_', participants[i + 1])
                        mermaid_lines.append(f'    {src}->>{dst}: {message}')
                        break
            
            # Left arrow responses
            elif '<──' in line or '<───' in line or '<────' in line or '←' in line:
                message = 'Response'
                
                # Check SIP response codes
                for code, desc in SIP_KNOWLEDGE['response_codes'].items():
                    if f'{code} {desc}' in line or f'{code}' in line[:20]:
                        message = f'{code} {desc}'
                        if current_time:
                            message = f'{code} {desc} [{current_time}]'
                        break
                
                # Check for request methods in responses
                if message == 'Response':
                    for method in SIP_KNOWLEDGE['request_methods']:
                        if method in line.upper():
                            message = f'200 OK ({method})'
                            break
                
                if len(participants) >= 2:
                    for i in range(len(participants) - 1, 0, -1):
                        src = re.sub(r'[^a-zA-Z0-9_]', '_', participants[i])
                        dst = re.sub(r'[^a-zA-Z0-9_]', '_', participants[i - 1])
                        mermaid_lines.append(f'    {src}-->>{dst}: {message}')
                        break
            
            # Process notes
            elif any(char in line for char in ['┌', '├', '└']):
                note_text = re.sub(r'[┌├└─]', '', line).strip()
                if note_text and len(note_text) > 3 and len(participants) >= 2:
                    participant = re.sub(r'[^a-zA-Z0-9_]', '_', participants[1])
                    # Limit note length
                    if len(note_text) > 50:
                        note_text = note_text[:47] + '...'
                    mermaid_lines.append(f'    Note over {participant}: {note_text}')
        
        mermaid_lines.append('```')
        return '\n'.join(mermaid_lines)
    
    def detect_simple_table(lines):
        """Detect if this is a simple data table."""
        potential_table = []
        for line in lines:
            cols = re.split(r'\s{2,}', line.strip())
            if len(cols) > 1:
                potential_table.append(cols)
        
        if len(potential_table) >= 2:
            col_counts = [len(row) for row in potential_table]
            # Check for consistent columns
            return max(col_counts) - min(col_counts) <= 1
        return False
    
    def convert_table_to_markdown(lines):
        """Convert ASCII table to markdown table."""
        potential_table = []
        for line in lines:
            cols = re.split(r'\s{2,}', line.strip())
            if len(cols) > 1:
                potential_table.append(cols)
        
        max_cols = max(len(row) for row in potential_table)
        table_lines = []
        
        # Header
        header = potential_table[0]
        while len(header) < max_cols:
            header.append('')
        table_lines.append('| ' + ' | '.join(header) + ' |')
        
        # Separator
        table_lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
        
        # Data rows
        for row in potential_table[1:]:
            while len(row) < max_cols:
                row.append('')
            table_lines.append('| ' + ' | '.join(row) + ' |')
        
        return '\n' + '\n'.join(table_lines) + '\n'
    
    def process_code_block_with_context(match, preceding_heading):
        code_content = match.group(1)
        lines = code_content.strip().split('\n')
        
        if len(lines) < 2:
            return match.group(0)
        
        # Use heading context to guide conversion
        heading_suggests_topology = should_convert_topology(preceding_heading)
        heading_suggests_signaling = should_convert_signaling(preceding_heading)
        
        # Priority 1: Heading suggests topology + content matches
        if heading_suggests_topology and detect_network_topology(lines):
            converted = convert_topology_to_mermaid(lines)
            if converted:
                return '\n' + converted + '\n'
        
        # Priority 2: Heading suggests signaling + content matches  
        if heading_suggests_signaling and detect_sip_signaling(lines):
            return '\n' + convert_sip_signaling_to_mermaid(lines) + '\n'
        
        # Priority 3: Auto-detect without heading context (stricter criteria)
        if not heading_suggests_topology and not heading_suggests_signaling:
            # Only convert if very strong signals
            if detect_network_topology(lines):
                converted = convert_topology_to_mermaid(lines)
                if converted:
                    return '\n' + converted + '\n'
            
            if detect_sip_signaling(lines):
                return '\n' + convert_sip_signaling_to_mermaid(lines) + '\n'
        
        # Priority 4: Check for simple table
        if detect_simple_table(lines):
            return convert_table_to_markdown(lines)
        
        # Keep original
        return match.group(0)
    
    # Process code blocks with context awareness
    result = []
    last_end = 0
    
    for match in re.finditer(r'```\n(.*?)\n```', content, flags=re.DOTALL):
        # Add content before this code block
        result.append(content[last_end:match.start()])
        
        # Get preceding heading
        preceding_heading = get_preceding_heading(content, match.start())
        
        # Process the code block with context
        processed = process_code_block_with_context(match, preceding_heading)
        result.append(processed)
        
        last_end = match.end()
    
    # Add remaining content
    result.append(content[last_end:])
    
    return ''.join(result)

# ============================================================================
# HELPER FUNCTIONS FOR NEW FEATURES (v1.4.0)
# ============================================================================

def convert_docx_to_html(docx_path: Path) -> str:
    """Convert Word document to HTML using mammoth."""
    if not WORD_INPUT_AVAILABLE:
        raise Exception("mammoth library not available")
    
    logger.info(f"Converting Word document: {docx_path}")
    try:
        with open(docx_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html_content = result.value
            
            # Log any messages/warnings from conversion
            if result.messages:
                for msg in result.messages:
                    logger.warning(f"Mammoth conversion message: {msg}")
            
            logger.info(f"Successfully converted Word document, size: {len(html_content)} bytes")
            return html_content
    except Exception as e:
        logger.error(f"Failed to convert Word document: {e}", exc_info=True)
        raise

def process_links_in_html(html_content: str, base_path: Path = None, is_preview: bool = False) -> str:
    """
    Process all links in HTML to ensure they are clickable and properly resolved.
    - External links open in new tab
    - Relative links resolved based on document location
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href', '')
            
            if not href:
                continue
            
            # External links - open in new tab
            if href.startswith('http://') or href.startswith('https://'):
                a_tag['target'] = '_blank'
                a_tag['rel'] = 'noopener noreferrer'
                logger.debug(f"External link: {href}")
            
            # Email links
            elif href.startswith('mailto:'):
                pass  # Already functional
            
            # Anchor links within document
            elif href.startswith('#'):
                pass  # Work as-is
            
            # Absolute paths
            elif href.startswith('/'):
                pass  # Already absolute
            
            # Relative links - resolve based on document location
            else:
                if base_path:
                    try:
                        # Resolve relative to document's directory
                        resolved = (base_path / href).resolve()
                        
                        # Check if it exists and is within MD_FOLDER
                        if resolved.exists() and resolved.is_relative_to(MD_FOLDER):
                            rel_path = resolved.relative_to(MD_FOLDER)
                            a_tag['href'] = f'/file/{rel_path}'
                            logger.debug(f"Resolved relative link {href} -> /file/{rel_path}")
                        else:
                            # Link target doesn't exist or outside workspace
                            a_tag['class'] = (a_tag.get('class', []) or []) + ['broken-link']
                            a_tag['title'] = 'Link target not found'
                            a_tag['style'] = 'color: #dc2626; text-decoration: underline dotted;'
                            logger.warning(f"Broken link: {href} (resolved to {resolved})")
                    except Exception as e:
                        logger.warning(f"Failed to resolve link {href}: {e}")
        
        return str(soup)
    except Exception as e:
        logger.error(f"Error processing links: {e}", exc_info=True)
        return html_content  # Return original if processing fails

def is_safe_workspace(path: Path) -> bool:
    """Check if directory is safe to use as workspace."""
    try:
        path = path.resolve()
        
        # Blocked directories (Windows)
        blocked = [
            Path('C:\\Windows'),
            Path('C:\\Program Files'),
            Path('C:\\Program Files (x86)'),
            Path.home() / 'AppData',
        ]
        
        # Check against blocked paths
        for blocked_path in blocked:
            try:
                if path == blocked_path or path.is_relative_to(blocked_path):
                    return False
            except:
                pass
        
        # Must have read permission
        try:
            list(path.iterdir())  # Test read access
        except PermissionError:
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error checking workspace safety: {e}")
        return False

def sanitize_log_content(content: str) -> str:
    """Remove sensitive information from logs."""
    # Remove IP addresses
    content = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP_ADDRESS>', content)
    # Remove full file paths - keep only filenames
    content = re.sub(r'[A-Z]:\\[^\s\'"]+', '<PATH>', content)
    content = re.sub(r'/[^\s\'"]+/[^\s\'"]+', '<PATH>', content)
    return content

# wkhtmltopdf management functions
WKHTMLTOPDF_VERSION = '0.12.6'
WKHTMLTOPDF_DOWNLOAD_URL = f'https://github.com/wkhtmltopdf/packaging/releases/download/{WKHTMLTOPDF_VERSION}/wkhtmltox-{WKHTMLTOPDF_VERSION}-1.msvc2015-win64.exe'

def find_wkhtmltopdf() -> str:
    """Find wkhtmltopdf executable, return path or None."""
    # Check common paths
    possible_paths = [
        r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
        PROJECT_ROOT / 'bin' / 'wkhtmltopdf.exe',  # Portable
    ]
    
    for path in possible_paths:
        path_obj = Path(path) if not isinstance(path, Path) else path
        if path_obj.exists():
            logger.info(f"Found wkhtmltopdf at {path_obj}")
            return str(path_obj)
    
    # Check PATH
    try:
        import shutil
        path_exe = shutil.which('wkhtmltopdf')
        if path_exe:
            logger.info(f"Found wkhtmltopdf in PATH: {path_exe}")
            return path_exe
    except:
        pass
    
    logger.warning("wkhtmltopdf not found")
    return None

def install_wkhtmltopdf_portable() -> str:
    """Download portable version and extract to app folder."""
    try:
        logger.info("Installing portable wkhtmltopdf...")
        portable_url = f'https://github.com/wkhtmltopdf/packaging/releases/download/{WKHTMLTOPDF_VERSION}/wkhtmltox-{WKHTMLTOPDF_VERSION}-1.msvc2015-win64.zip'
        
        import zipfile
        zip_path = tempfile.mktemp(suffix='.zip')
        logger.info(f"Downloading from {portable_url}")
        urllib.request.urlretrieve(portable_url, zip_path)
        
        bin_folder = PROJECT_ROOT / 'bin'
        bin_folder.mkdir(exist_ok=True)
        
        logger.info(f"Extracting to {bin_folder}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(bin_folder)
        
        # Find extracted exe
        exe_path = bin_folder / 'bin' / 'wkhtmltopdf.exe'
        if not exe_path.exists():
            # Try alternate structure
            for item in bin_folder.rglob('wkhtmltopdf.exe'):
                exe_path = item
                break
        
        if exe_path.exists():
            logger.info(f"Portable wkhtmltopdf installed at {exe_path}")
            return str(exe_path)
        
        raise Exception("wkhtmltopdf.exe not found after extraction")
    
    except Exception as e:
        logger.error(f"Portable installation failed: {e}", exc_info=True)
        raise

# ============================================================================
# END HELPER FUNCTIONS
# ============================================================================

def render_document_from_file(md_file_path: Path, enable_experimental: bool = False) -> str:
    """Read a document file (markdown or Word), apply feature pipeline, then render HTML."""
    try:
        # Check file size before reading
        file_size = md_file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            logger.warning(f"File too large: {md_file_path} ({size_mb:.2f} MB)")
            return f"<div style='padding: 20px; background: #fee; border: 2px solid #f00; border-radius: 8px;'>"\
                   f"<h2>⚠️ File Too Large</h2>"\
                   f"<p>This file is <strong>{size_mb:.2f} MB</strong>, which exceeds the maximum supported size of <strong>{max_mb:.0f} MB</strong>.</p>"\
                   f"<p><strong>Suggestions:</strong></p>"\
                   f"<ul>"\
                   f"<li>Split the file into smaller documents</li>"\
                   f"<li>Remove unnecessary content or images</li>"\
                   f"<li>Open the file in a text editor instead</li>"\
                   f"</ul></div>"
        
        # Handle Word documents (.docx)
        if md_file_path.suffix.lower() == '.docx':
            if not WORD_INPUT_AVAILABLE:
                logger.error("Word input attempted but mammoth not available")
                return "<p>Word document support not available. Please install mammoth library.</p>"
            
            try:
                html_content = convert_docx_to_html(md_file_path)
                # Process links in the HTML
                html_content = process_links_in_html(html_content, base_path=md_file_path.parent)
                logger.info(f"Successfully rendered Word document: {md_file_path}")
                return html_content, ""
            except Exception as e:
                logger.error(f"Failed to render Word document {md_file_path}: {e}", exc_info=True)
                return f"<p>Error converting Word document: {str(e)}</p>", ""
        
        # Handle text/markdown files
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
            
        logger.info(f"Rendering document: {md_file_path}, size: {len(md_text)} bytes")
        
    except Exception as e:
        logger.error(f"Error reading file {md_file_path}: {e}", exc_info=True)
        return f"<p>Error reading file: {str(e)}</p>", ""

    # Apply markdown processing pipeline
    pipeline = FEATURES.build_pipeline(enable_experimental=enable_experimental)
    processed = run_pipeline(md_text, pipeline)
    html_content, toc_content = render_baseline(processed)
    
    # Process links in the rendered HTML
    html_content = process_links_in_html(html_content, base_path=md_file_path.parent)
    
    return html_content, toc_content

@app.route('/')
def index():
    """Main page displaying list ofmarkdown files and folders."""
    folder = request.args.get('folder', '').strip()
    
    # Use non-recursive mode to browse specific folder
    items = get_markdown_files(subdir=folder, recursive=False)
    
    logger.info(f"Index route (folder='{folder}'): Found {len(items)} items")
    return render_template('index.html', files=items, md_folder=str(MD_FOLDER), current_folder=folder, version=VERSION)

@app.route('/debug/info')
def debug_info():
    """Debug endpoint to show configuration and file discovery."""
    import os
    md_files = get_markdown_files()
    return jsonify({
        'project_root': str(PROJECT_ROOT),
        'md_folder': str(MD_FOLDER),
        'md_folder_exists': MD_FOLDER.exists(),
        'frozen': getattr(sys, 'frozen', False),
        'executable_path': sys.executable,
        'cwd': os.getcwd(),
        'version': VERSION,
        'file_count': len(md_files),
        'files': [{'name': f['name'], 'path': str(f.get('path', 'N/A'))} for f in md_files],
        'config': CONFIG
    })

@app.route('/raw/<path:filename>')
def serve_raw_file(filename):
    """Serve a raw file from the workspace (for PDF embedding etc)."""
    # Security: Ensure we are inside MD_FOLDER
    try:
        file_path = (MD_FOLDER / filename).resolve()
        # Security check to prevent path traversal
        # pathlib .resolve() handles '..' but we must ensure it starts with MD_FOLDER
        if not str(file_path).startswith(str(MD_FOLDER.resolve())):
             abort(403, description="Access outside workspace denied")
             
        if not file_path.exists():
            abort(404)
            
        return send_from_directory(MD_FOLDER, filename)
    except Exception as e:
        logger.error(f"Error serving raw file {filename}: {e}")
        abort(404)

@app.route('/file/<path:filename>')
def view_file(filename):
    """View a specific markdown file."""
    md_path = Path(MD_FOLDER)
    
    # Smart features temporarily disabled - coming in v1.1/1.2
    # See doc/FUTURE_FEATURES.md for details
    enable_experimental = False  # TODO: Re-enable with proper UI in future release
    
    # Handle both direct filename and relative path
    file_path = None
    
    # Try as relative path first
    potential_path = md_path / filename
    if potential_path.exists() and potential_path.is_file():
        file_path = potential_path
    else:
        # Try adding .md extension
        potential_path = md_path / f"{filename}.md"
        if potential_path.exists():
            file_path = potential_path
        else:
            # Search recursively for matching file
            for f in md_path.rglob('*'):
                if f.is_file() and (f.stem == filename or f.name == filename or str(f.relative_to(md_path)) == filename):
                    file_path = f
                    break
    
    if not file_path or not file_path.exists():
        abort(404)
    
    # Handle PDF Files (Native Embedding)
    if file_path.suffix.lower() == '.pdf':
        stat = file_path.stat()
        file_info = {
            'name': file_path.stem,
            'filename': file_path.name,
            'relative_path': str(file_path.relative_to(MD_FOLDER)),
            'content': f'''
                <div class="pdf-container" style="height: calc(100vh - 140px); width: 100%; overflow: hidden; border-radius: 8px; border: 1px solid var(--border-color);">
                    <iframe src="/raw/{str(file_path.relative_to(MD_FOLDER)).replace('\\', '/')}" width="100%" height="100%" style="border:none;">
                    </iframe>
                </div>
            ''',
            'toc': "", # PDFs handle their own TOC usually
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'size': f"{stat.st_size / 1024:.2f} KB",
            'type': 'pdf'
        }
        return render_template('view.html', file=file_info, version=VERSION)

    # Convert to HTML via feature pipeline (baseline + optional experimental)
    html_content, toc_content = render_document_from_file(file_path, enable_experimental=enable_experimental)
    stat = file_path.stat()
    
    file_info = {
        'name': file_path.stem,
        'filename': file_path.name,
        'relative_path': str(file_path.relative_to(MD_FOLDER)),
        'content': html_content,
        'toc': toc_content,
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'size': f"{stat.st_size / 1024:.2f} KB"
    }
    
    return render_template('view.html', file=file_info, version=VERSION)

def get_documentation_files():
    """Get list of available documentation files."""
    if not DOCS_FOLDER.exists():
        return []
    
    docs = []
    for f in DOCS_FOLDER.glob('*.md'):
        if f.name.lower() != 'readme.md':  # Exclude raw readme if user guide exists
             docs.append({
                 'name': f.stem.replace('_', ' ').title(),
                 'filename': f.name,
                 'active': False
             })
    # Sort: User Guide first, then alphabetical
    docs.sort(key=lambda x: (x['filename'] != 'USER_GUIDE.md', x['name']))
    return docs

@app.route('/docs')
@app.route('/docs/<path:filename>')
def documentation(filename=None):
    """Serve the documentation page."""
    if not filename:
        filename = 'USER_GUIDE.md'
    
    # Security: Ensure filename is just a name, not a path
    filename = Path(filename).name
    docs_path = Path(DOCS_FOLDER) / filename
    
    if not docs_path.exists():
        # Fallback to USER_GUIDE if specific file not found, or 404
        if filename != 'USER_GUIDE.md' and (Path(DOCS_FOLDER) / 'USER_GUIDE.md').exists():
             return redirect(url_for('documentation'))
        abort(404, description="Documentation not found")
    
    # Convert documentation markdown to HTML
    html_content, toc_content = render_document_from_file(docs_path, enable_experimental=False)
    
    # Get navigation list
    nav_items = get_documentation_files()
    for item in nav_items:
        if item['filename'] == filename:
            item['active'] = True
            
    doc_info = {
        'name': filename.replace('.md', '').replace('_', ' ').title(),
        'filename': filename,
        'content': html_content,
        'toc': toc_content,
        'version': VERSION
    }
    
    return render_template('docs.html', doc=doc_info, nav_items=nav_items, version=VERSION)

@app.route('/preview', methods=['POST'])
def preview_file():
    """Preview a document file uploaded from user's filesystem."""
    # Accept file upload via multipart/form-data (better for large files)
    if 'file' in request.files:
        file = request.files['file']
        if not file or file.filename == '':
            abort(400, description="No file provided")
        
        filename = file.filename
        file_ext = Path(filename).suffix.lower()
        
        # Handle Word documents
        if file_ext == '.docx':
            if not WORD_INPUT_AVAILABLE:
                return {
                    "error": "Word Document Support Not Available",
                    "message": "The mammoth library is not installed.",
                    "details": "Please install mammoth to view Word documents."
                }, 503
            
            try:
                # Save to temp file for mammoth processing
                temp_dir = PROJECT_ROOT / 'temp_uploads'
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / filename
                file.save(temp_path)
                
                # Store in session for link resolution
                session['preview_base_path'] = str(temp_path.parent)
                session['preview_filename'] = filename
                
                # Convert Word to HTML
                html_content = convert_docx_to_html(temp_path)
                html_content = process_links_in_html(html_content, base_path=temp_path.parent, is_preview=True)
                
                file_info = {
                    'name': Path(filename).stem,
                    'filename': filename,
                    'content': html_content,
                    'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'size': f"{temp_path.stat().st_size / 1024:.2f} KB",
                    'preview_mode': True
                }
                
                return render_template('view.html', file=file_info, version=VERSION)
                
            except Exception as e:
                logger.error(f"Error processing Word document: {e}", exc_info=True)
                return {
                    "error": "Word Document Conversion Failed",
                    "message": str(e),
                    "filename": filename
                }, 500
        
        # Handle PDF Files (Bypass Text Decoding)
        if filename.lower().endswith('.pdf'):
            try:
                # Save to temp
                temp_dir = Path(app.config['UPLOAD_FOLDER']) / 'temp'
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_filename = secure_filename(filename)
                temp_path = temp_dir / temp_filename
                file.save(temp_path)
                
                # Register for cleanup (handled by session/OS mostly, but good to note)
                session['preview_filename'] = filename
                
                # Construct file info mimicking view_file
                file_info = {
                    'name': Path(filename).stem,
                    'filename': filename,
                    'relative_path': f"temp/{temp_filename}", # Virtual path
                    'content': f'''
                        <div class="pdf-container" style="height: calc(100vh - 190px); width: 100%; overflow: hidden; border-radius: 8px; border: 1px solid var(--border-color);">
                            <!-- Use a route that serves from temp or raw if confirmed -->
                            <!-- For preview, we might need a specific temp route or just serve_raw if we move it to MD_FOLDER temporarily -->
                            <!-- CURRENTLY: Preview uploads shouldn't go to MD_FOLDER until Saved. -->
                            <!-- We need a route to serve temp/preview files. -->
                            <div style="padding: 2rem; text-align: center; color: var(--text-muted);">
                                <i class="fas fa-file-pdf" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                                <p>PDF Preview is available after saving.</p>
                                <p style="font-size: 0.8rem;">To view this PDF, please save it to your workspace.</p>
                            </div>
                        </div>
                    ''',
                    'toc': "",
                    'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'size': f"{temp_path.stat().st_size / 1024:.2f} KB",
                    'type': 'pdf',
                    'preview_mode': True
                }
                return render_template('view.html', file=file_info, version=VERSION)
            except Exception as e:
                logger.error(f"Error handling PDF preview: {e}")
                return {"error": "PDF Preview Failed", "message": str(e)}, 500

        # Handle text/markdown files
        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return {
                "error": "Invalid File Encoding",
                "message": "The file must be encoded in UTF-8.",
                "details": "Please save your file as UTF-8 and try again."
            }, 400
    else:
        # Fallback: accept content via form POST (legacy support)
        content = request.form.get('content', '')
        filename = request.form.get('filename', 'Untitled.md')
        if not content:
            abort(400, description="No content provided")
    
    # Check actual content size
    content_size = len(content.encode('utf-8'))
    if content_size > MAX_FILE_SIZE:
        size_mb = content_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return {
            "error": "File Too Large",
            "message": f"The file content is {size_mb:.2f} MB, which exceeds the maximum of {max_mb:.0f} MB.",
            "details": "Please split the file into smaller documents or reduce its size.",
            "filename": filename,
            "size_mb": f"{size_mb:.2f}",
            "max_mb": f"{max_mb:.0f}"
        }, 413
    
    # Smart features disabled - using baseline rendering only
    enable_experimental = False
    
    # Use same feature pipeline as file view
    pipeline = FEATURES.build_pipeline(enable_experimental=enable_experimental)
    processed = run_pipeline(content, pipeline)
    html_content, toc_content = render_baseline(processed)
    html_content = process_links_in_html(html_content, base_path=MD_FOLDER, is_preview=True)
    
    file_info = {
        'name': Path(filename).stem,
        'filename': filename,
        'content': html_content,
        'toc': toc_content,
        'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'size': f"{len(content) / 1024:.2f} KB",
        'preview_mode': True
    }
    
    return render_template('view.html', file=file_info, version=VERSION)

@app.route('/api/export/<format_ext>', methods=['POST'])
def handle_export_request(format_ext):
    """
    Generic export handler. Delegates to registered plugins.
    """
    try:
        data = request.json
        html_content = data.get('html', '')
        # filename = data.get('filename') # handled by frontend download logic or Content-Disposition
        
        # Resolve Handler
        handler = FEATURES.get_export_handler(format_ext)
        logger.debug(f"Handle Export Request: Resolved handler for {format_ext} -> {handler}")
        
        if not handler:
            # Return specific error for frontend "Upsell" logic
            return jsonify({
                "error": "Export plugin not installed", 
                "code": "MISSING_PLUGIN",
                "plugin_name": f"docnexus-plugin-{format_ext}",
                "message": f" The {format_ext.upper()} export plugin is not installed."
            }), 404
            
        # Execute Handler
        # Handler signature: (html_content: str) -> bytes
        try:
            output_data = handler(html_content)
        except Exception as e:
            logger.error(f"Plugin handler failed: {e}", exc_info=True)
            return jsonify({"error": f"Plugin Execution Failed: {str(e)}"}), 500
        
        if not output_data:
             return jsonify({"error": "Export handler returned no data"}), 500

        # Determine Mime Type
        mime_type = "application/octet-stream"
        if format_ext == 'pdf':
            mime_type = "application/pdf"
        elif format_ext == 'docx':
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        from io import BytesIO
        return send_file(
            BytesIO(output_data),
            mimetype=mime_type,
            as_attachment=True,
            download_name=f"export.{format_ext}"
        )

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/search')
def search():
    """Search through markdown files."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return {'results': []}
    
    query_lower = query.lower()
    results = []
    md_files = get_markdown_files()
    
    for file_info in md_files:
        # Search in filename
        if query_lower in file_info['name'].lower() or query_lower in file_info['filename'].lower():
            results.append({
                'name': file_info['name'],
                'filename': file_info['filename'],
                'path': file_info['relative_path'],
                'folder': file_info['folder'],
                'match_type': 'filename',
                'snippet': f"Found in filename: {file_info['filename']}"
            })
            continue
        
        # Search in file content
        try:
            with open(file_info['path'], 'r', encoding='utf-8') as f:
                content = f.read()
                if query_lower in content.lower():
                    # Find context snippet
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            # Get context (line before, match line, line after)
                            start = max(0, i - 1)
                            end = min(len(lines), i + 2)
                            snippet = ' '.join(lines[start:end]).strip()
                            if len(snippet) > 150:
                                snippet = snippet[:150] + '...'
                            
                            results.append({
                                'name': file_info['name'],
                                'filename': file_info['filename'],
                                'path': file_info['relative_path'],
                                'folder': file_info['folder'],
                                'match_type': 'content',
                                'snippet': snippet,
                                'line': i + 1
                            })
                            break  # Only show first match per file
        except Exception as e:
            print(f"Error searching file {file_info['path']}: {e}")
            continue
    
    return {'results': results, 'query': query, 'count': len(results)}

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

# Legacy save_document/get_source routes removed and migrated to 'editor' plugin.

@app.route('/api/workspaces', methods=['GET'])
def get_workspaces():
    """Get list of configured workspaces."""
    try:
        config = load_config()
        return jsonify({
            'workspaces': config['workspaces'],
            'active': config['active_workspace'],
            'recent': config.get('recent_workspaces', [])
        })
    except Exception as e:
        logger.error(f"Error getting workspaces: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/workspaces', methods=['POST'])
def add_workspace():
    """Add new workspace directory."""
    try:
        data = request.get_json()
        workspace_path = data.get('path')
        
        if not workspace_path:
            return jsonify({'error': 'Missing workspace path'}), 400
        
        path_obj = Path(workspace_path)
        
        if not path_obj.exists():
            return jsonify({'error': 'Directory does not exist'}), 400
        
        if not path_obj.is_dir():
            return jsonify({'error': 'Path is not a directory'}), 400
        
        # Security checks
        if not is_safe_workspace(path_obj):
            logger.warning(f"Unsafe workspace rejected: {workspace_path}")
            return jsonify({'error': 'Access to this directory is not allowed for security reasons'}), 403
        
        # Add to config
        config = load_config()
        workspace_str = str(path_obj.resolve())
        
        if workspace_str not in config['workspaces']:
            config['workspaces'].append(workspace_str)
            save_config(config)
            logger.info(f"Workspace added: {workspace_str}")
        
        return jsonify({'success': True, 'workspace': workspace_str})
    
    except Exception as e:
        logger.error(f"Error adding workspace: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/workspaces/active', methods=['POST'])
def set_active_workspace():
    """Switch active workspace."""
    try:
        data = request.get_json()
        workspace_path = data.get('path')
        
        if not workspace_path:
            return jsonify({'error': 'Missing workspace path'}), 400
        
        # Resolve path to ensure it matches stored format
        path_obj = Path(workspace_path).resolve()
        workspace_str = str(path_obj)
        
        config = load_config()
        
        if workspace_str not in config['workspaces']:
            return jsonify({'error': f'Workspace not configured: {workspace_str}'}), 400
        
        config['active_workspace'] = workspace_str
        
        # Update recent list
        if 'recent_workspaces' not in config:
            config['recent_workspaces'] = []
        
        if workspace_path in config['recent_workspaces']:
            config['recent_workspaces'].remove(workspace_path)
        
        config['recent_workspaces'].insert(0, workspace_path)
        config['recent_workspaces'] = config['recent_workspaces'][:5]  # Keep last 5
        
        save_config(config)
        
        # Update global MD_FOLDER
        global MD_FOLDER
        MD_FOLDER = Path(workspace_path)
        
        logger.info(f"Active workspace changed to: {workspace_path}")
        return jsonify({'success': True, 'active_workspace': workspace_path})
    
    except Exception as e:
        logger.error(f"Error setting active workspace: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/workspaces/<path:workspace_path>', methods=['DELETE'])
def delete_workspace(workspace_path):
    """Remove workspace from configuration."""
    try:
        config = load_config()
        
        if workspace_path in config['workspaces']:
            # Prevent deleting active workspace
            if workspace_path == config['active_workspace']:
                return jsonify({'error': 'Cannot delete active workspace'}), 400
            
            config['workspaces'].remove(workspace_path)
            save_config(config)
            logger.info(f"Workspace removed: {workspace_path}")
            return jsonify({'success': True})
        
        return jsonify({'error': 'Workspace not found'}), 404
    
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/install-wkhtmltopdf', methods=['POST'])
def api_install_wkhtmltopdf():
    """Endpoint to trigger wkhtmltopdf installation."""
    try:
        data = request.get_json()
        mode = data.get('mode', 'portable')  # 'portable' or 'system'
        
        logger.info(f"wkhtmltopdf installation requested: mode={mode}")
        
        if mode == 'portable':
            exe_path = install_wkhtmltopdf_portable()
            if exe_path:
                return jsonify({'success': True, 'path': str(exe_path)})
        else:
            # System install requires admin privileges - not implemented
            return jsonify({'success': False, 'error': 'System installation not implemented'}), 501
        
        return jsonify({'success': False, 'error': 'Installation failed'}), 500
    
    except Exception as e:
        logger.error(f"Installation error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browse-folder', methods=['GET'])
def browse_folder():
    """Open native folder browser dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create and hide root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Open folder dialog
        folder_path = filedialog.askdirectory(
            title='Select Workspace Folder',
            mustexist=True
        )
        
        root.destroy()
        
        if folder_path:
            return jsonify({'success': True, 'path': folder_path})
        else:
            return jsonify({'success': False, 'message': 'No folder selected'}), 400
            
    except ImportError:
        logger.warning("tkinter not available for native folder browser")
        return jsonify({'error': 'Native folder browser not available. Please enter path manually.'}), 501
    except Exception as e:
        logger.error(f"Error opening folder browser: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ============================================================================
# END NEW ROUTES
# ============================================================================



@app.route('/extensions')
def extensions_page():
    return render_template('extensions.html', version=VERSION)

@app.route('/api/search')
def search_files():
    """Full-text search through workspace documents."""
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])
    
    matches = []
    # Reuse existing logic to get file list
    all_files = get_markdown_files()
    
    for file_info in all_files:
        # Check filename match first (fastest)
        # Note: 'name' is filename without extension, 'filename' is with extension
        # We search both to be safe
        if query in file_info['name'].lower() or query in file_info['filename'].lower():
            matches.append(file_info['relative_path'])
            continue
            
        # Check content match
        file_path = file_info.get('path')
        
        # Only search text-based files
        if file_path and file_path.suffix.lower() in ['.md', '.txt', '.markdown']:
            # Explicitly exclude .pdf/.docx (not indexable yet)

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if query in content:
                        matches.append(file_info['relative_path'])
            except Exception:
                continue # Skip unreadable files
                
    return jsonify(matches)


@app.route('/api/debug/features', methods=['GET'])
def debug_features():
    features_list = []
    if FEATURES and FEATURES._features:
        for f in FEATURES._features:
            features_list.append({
                "name": f.name,
                "type": str(f.type),
                "state": str(f.state)
            })
    return jsonify({
        "count": len(features_list),
        "features": features_list,
        "registry_plugins": [str(p) for p in PluginRegistry().get_all_plugins()] if PluginRegistry() else []
    })

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)
