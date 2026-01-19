from flask import Blueprint, request, jsonify, abort, current_app
from pathlib import Path
import shutil
import logging
import sys
from docnexus.features.registry import Feature, FeatureType, FeatureState

# Create Blueprint
# Create Blueprint
editor_bp = Blueprint('editor', __name__)
blueprint = editor_bp
logger = logging.getLogger(__name__)

def get_config():
    """Deferred import to avoid circular dependency/init issues."""
    from docnexus.app import MD_FOLDER, ALLOWED_EXTENSIONS
    return MD_FOLDER, ALLOWED_EXTENSIONS

@editor_bp.route('/api/get-source/<path:filename>')
def get_source(filename):
    """Get original source content for editing."""
    logger.debug(f"Editor: Handling get-source request for: {filename}")
    MD_FOLDER, ALLOWED_EXTENSIONS = get_config()
    
    try:
        file_path = MD_FOLDER / filename
        
        if not file_path.exists() or file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            logger.warning(f"Editor: Source file not found or invalid: {file_path}")
            return jsonify({'error': 'File not found or invalid type', 'path': str(filename)}), 404
        
        # Don't allow editing Word files
        if file_path.suffix.lower() == '.docx':
            return jsonify({'error': 'Word documents cannot be edited directly'}), 400
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Editor: Served source for: {filename} ({len(content)} bytes)")
        return jsonify({'content': content, 'path': str(filename)})
    
    except Exception as e:
        logger.error(f"Editor: Error reading source {filename}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@editor_bp.route('/api/save-document', methods=['POST'])
def save_document():
    """Save edited document with backup."""
    MD_FOLDER, ALLOWED_EXTENSIONS = get_config()
    
    try:
        data = request.get_json()
        filename = data.get('filename')
        content = data.get('content')
        
        if not filename or content is None:
            return jsonify({'error': 'Missing filename or content'}), 400
        
        # Security: Prevent directory traversal
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            logger.warning(f"Attempted directory traversal: {filename}")
            return jsonify({'error': 'Invalid filename'}), 403
        
        file_path = MD_FOLDER / filename
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        try:
            shutil.copy(file_path, backup_path)
            logger.info(f"Editor: Backup created: {backup_path}")
        except Exception as e:
            logger.error(f"Editor: Failed to create backup: {e}")
            return jsonify({'error': 'Failed to create backup'}), 500
        
        # Write new content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Editor: Document saved: {filename}, size: {len(content)} bytes")
            return jsonify({'success': True, 'backup': str(backup_path), 'size': len(content)})
        except Exception as e:
            # Restore from backup if write failed
            if backup_path.exists():
                shutil.copy(backup_path, file_path)
            logger.error(f"Editor: Failed to save document: {e}")
            return jsonify({'error': 'Failed to save document'}), 500
    
    except Exception as e:
        logger.error(f"Error in save_document: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def get_features():
    """Register the Editor functionality."""
    return [
        Feature(
            name="Doc Editor",
            handler=None,
            state=FeatureState.STANDARD,
            feature_type=FeatureType.UI_EXTENSION,
            meta={"source": "bundled"}
        )
    ]

# Expose Blueprint for the loader to pick up

# Metadata
PLUGIN_METADATA = {
    'name': 'Doc Editor',
    'description': 'Professional WYSIWYG editor with live markdown preview, advanced formatting, and real-time collaboration tools.',
    'category': 'editor',
    'icon': 'fa-edit',
    'preinstalled': True
}
