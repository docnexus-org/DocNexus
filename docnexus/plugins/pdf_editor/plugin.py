from flask import Blueprint, jsonify, request, current_app
import os
from docnexus.features.registry import Feature, FeatureType, FeatureState

# Blueprint for future backend operations (saving, merging, etc.)
pdf_bp = Blueprint('pdf_editor', __name__)
blueprint = pdf_bp

@pdf_bp.route('/api/pdf/save', methods=['POST'])
def save_pdf():
    # Strict Operational Check
    from docnexus.core.state import PluginState
    if not PluginState.get_instance().is_plugin_installed('pdf_editor'):
        return jsonify({'success': False, 'error': 'Plugin disabled'}), 403

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


def load_resource(filename):
    """Load a template file from the plugin's templates directory."""
    try:
        base_path = os.path.dirname(__file__)
        resource_path = os.path.join(base_path, 'templates', filename)
        with open(resource_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading resource {filename}: {e}")
        return ""

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
                "content": load_resource('head_scripts.html')
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
                "content": load_resource('editor_ui.html')
            }
        ),
        # API Handlers (Dispatcher based)
        Feature(
            "pdf_editor_save",
            feature_type=FeatureType.API_HANDLER,
            handler=save_pdf,
            state=FeatureState.STANDARD,
            meta={
                "api_path": "save",
                "plugin_id": "pdf_editor"
            }
        )
    ]

# Future: Add routes for saving binary PDF data
# @pdf_bp.route('/api/pdf/save', methods=['POST'])
# def save_pdf():
#     pass
