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
                "slot": "EDITOR_CONTAINER", # Target Slot
                "file_types": ["pdf"]
            }
        )
    ]

# Future: Add routes for saving binary PDF data
# @pdf_bp.route('/api/pdf/save', methods=['POST'])
# def save_pdf():
#     pass
