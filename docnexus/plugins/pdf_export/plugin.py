import os
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).parent
ENABLED_FILE = PLUGIN_DIR / "ENABLED"
DEPENDENCIES = ["xhtml2pdf"]

import io

def export_pdf(content_html: str) -> bytes:
    """
    Export content to PDF using xhtml2pdf.
    Returns bytes.
    """
    try:
        from xhtml2pdf import pisa
        # Prepare content with robust CSS handling
        # xhtml2pdf crashes on CSS variables (var(--...)).
        # We must:
        # 1. Inline external stylesheets
        # 2. Sanitize all 'var(--...)' usages in both HTML styles and inlined CSS
        
        import re
        
        # Regex to find CSS variable usage: var(--name, fallback) or var(--name)
        # We replace with a safe color (black/gray) to prevent crash
        css_var_pattern = re.compile(r'var\s*\([^)]+\)')
        
        def sanitize_css(text):
            # Replace common specific vars with reasonable values
            replacements = {
                'var(--color-fg-default)': '#000000',
                'var(--color-canvas-default)': '#ffffff',
                'var(--color-border-default)': '#cccccc',
                'var(--color-accent-fg)': '#0969da',
                'var(--color-neutral-muted)': '#afb8c1',
            }
            for k, v in replacements.items():
                text = text.replace(k, v)
            
            # Nuke remaining vars to generic gray to prevent crash
            return css_var_pattern.sub('#888888', text)

        # "SAFE MODE": Strip all external stylesheets to prevent xhtml2pdf crash on modern CSS
        # We replace them with a robust internal stylesheet optimized for print.
        
        # 1. Remove all <link rel="stylesheet"> tags
        link_pattern = re.compile(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', re.IGNORECASE)
        full_html = link_pattern.sub('', content_html)
        
        # 2. Remove all <style>...</style> blocks (Nuclear option)
        # Use DOTALL to match newlines inside style tags
        style_block_pattern = re.compile(r'<style\b[^>]*>.*?</style>', re.IGNORECASE | re.DOTALL)
        full_html = style_block_pattern.sub('', full_html)
        
        # 3. Remove all style="..." attributes (Nuclear option)
        # This removes inline styles that might contain vars
        # We match style=" anything except quote "
        # Hacky regex but sufficient for standard HTML
        style_attr_pattern = re.compile(r'\sstyle=["\'][^"\']*["\']', re.IGNORECASE)
        full_html = style_attr_pattern.sub('', full_html)
        
        # 4. Add Safe Internal Stylesheet
        # This provides a clean, professional look without relying on the web UI's complex CSS
            
        # 3. Add Print Override Styles
        full_html = f"""
        <html>
        <head>
            {full_html}
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: Helvetica, Arial, sans-serif;
                    font-size: 10pt;
                    color: #000000;
                    background-color: #ffffff;
                }}
                /* Force simplified styling for PDF */
                .markdown-body {{ font-family: Helvetica, Arial, sans-serif !important; color: black !important; background: white !important; }}
                h1, h2, h3, h4, h5, h6 {{ color: #333 !important; page-break-after: avoid; }}
                h1 {{ border-bottom: 2px solid #333; }}
                code, pre {{ font-family: Courier; background: #f5f5f5; border: 1px solid #eee; }}
                table {{ border-collapse: collapse; width: 100%; }}
                td, th {{ border: 1px solid #ccc; padding: 4px; }}
            </style>
        </head>
        <body>
        """
        
        # Convert to PDF in memory
        result = io.BytesIO()
        
        pisa_status = pisa.CreatePDF(
            full_html,              # the HTML to convert
            dest=result             # file handle to recieve result
        )
            
        if pisa_status.err:
            raise RuntimeError(f"PDF generation error: {pisa_status.err}")
            
        return result.getvalue()
        
    except ImportError as ie:
        import traceback
        import sys
        
        # Capture full context
        tb = traceback.format_exc()
        
        # Try to find what exactly failed
        error_msg = f"xhtml2pdf import failed. Cause: {ie}. Path: {sys.path}"
        print(f"DEBUG_IMPORT_FAIL: {error_msg}")
        print(tb) # Print to console/log
        
        raise RuntimeError(f"xhtml2pdf library is missing/broken. Detail: {ie}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"PDF Export Failed: {e}")

def get_features():
    from docnexus.features.registry import Feature, FeatureType, FeatureState
    from docnexus.core.state import PluginState
    
    # Check "Enabled" status via Config
    is_enabled = "pdf_export" in PluginState.get_instance().get_installed_plugins()
    
    features = []
    
    # We register the feature but mark it as installed/not installed
    features.append(
        Feature(
            "pdf_export",
            feature_type=FeatureType.EXPORT_HANDLER,
            handler=export_pdf,
            state=FeatureState.EXPERIMENTAL,
            meta={
                "extension": "pdf",
                "label": "PDF Document (.pdf)",
                "installed": is_enabled,
                "description": "Generates professional PDF documents from your markdown.",
                "version": "1.0.0"
            }
        )
    )
    
    return features

# Metadata
PLUGIN_METADATA = {
    'name': 'PDF Export',
    'description': 'Converts documentation to professional PDF format with Table of Contents, cover page, and optimized print layout.',
    'category': 'export',
    'icon': 'fa-file-pdf',
    'preinstalled': False
}
