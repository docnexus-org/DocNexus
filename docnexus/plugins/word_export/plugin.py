import logging
import io
import shutil
from pathlib import Path

# Note: Feature, FeatureType, FeatureState, PluginRegistry are INJECTED by the loader.
# Do not import them directly to avoid split-brain issues.

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

logger = logging.getLogger(__name__)

# Constants
MAX_EXPORT_HTML_SIZE = 50 * 1024 * 1024  # 50 MB

def add_bookmark(paragraph, bookmark_name):
    """Add a bookmark to a paragraph in a Word document."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    
    # Create bookmark start element
    bookmark_start = OxmlElement('w:bookmarkStart')
    bookmark_start.set(qn('w:id'), str(hash(bookmark_name) % 10000))
    bookmark_start.set(qn('w:name'), bookmark_name)
    
    # Create bookmark end element
    bookmark_end = OxmlElement('w:bookmarkEnd')
    bookmark_end.set(qn('w:id'), str(hash(bookmark_name) % 10000))
    
    # Insert bookmark
    paragraph._element.insert(0, bookmark_start)
    paragraph._element.append(bookmark_end)

def export_to_word(html_content: str) -> bytes:
    """
    Exports HTML content to a Word (.docx) file byte stream.
    """
    try:
        from htmldocx import HtmlToDocx
        from docx import Document
        from docx.shared import RGBColor, Pt
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as e:
        logger.error(f"Failed to import Word export dependencies: {e}")
        raise RuntimeError("Word export dependencies (htmldocx, python-docx) not installed.")

    # Size Check
    html_size = len(html_content.encode('utf-8'))
    if html_size > MAX_EXPORT_HTML_SIZE:
        raise ValueError(f"Content too large ({html_size/1024/1024:.2f} MB). Max {MAX_EXPORT_HTML_SIZE/1024/1024} MB.")

    logger.info(f"Generating Word Document from {html_size} bytes of HTML...")

    # Pre-process HTML with BeautifulSoup
    try:
        soup = BeautifulSoup(html_content, 'lxml')
    except:
        soup = BeautifulSoup(html_content, 'html.parser')
    
    # Cleaning (Scripts, Styles, Nav)
    for tag in soup.find_all(['script', 'style', 'nav']):
        tag.decompose()
    
    # Main Content Extraction
    main_content = soup.find(class_='markdown-content')
    if main_content:
        # Style Tables for Word
        for table in main_content.find_all('table'):
            table['style'] = 'border-collapse: collapse; width: 100%; border: 2px solid rgba(99, 102, 241, 0.2); margin-bottom: 20px;'
            table['border'] = '1'
            
            # Thead check
            thead = table.find('thead')
            if not thead:
                first_row = table.find('tr')
                if first_row and first_row.find('th'):
                    thead = soup.new_tag('thead')
                    first_row.extract()
                    thead.append(first_row)
                    table.insert(0, thead)
            
            # Colors and Styles injection (simplified for brevity, matching previous logic)
            for th in table.find_all('th'):
                th['bgcolor'] = '#6366f1'
                th['style'] = 'background-color: #6366f1 !important; color: #ffffff !important;'
            
            for td in table.find_all('td'):
                td['style'] = 'padding: 8px; border: 1px solid #e5e7eb;'

        # Clean HTML String
        clean_html = f'<html><head><meta charset="utf-8"></head><body>{str(main_content)}</body></html>'
    else:
        clean_html = f'<html><body>{soup.body.decode_contents() if soup.body else str(soup)}</body></html>'

    # Pre-process HTML to resolve image paths (crucial for PyInstaller/execution context)
    soup = BeautifulSoup(clean_html, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and not src.startswith(('http://', 'https://', 'data:')):
            # Resolve relative path to absolute
            # Attempt to find it relative to current working directory or known static folders
            # Logic: If path starts with /, it's usually valid if server root is CWD.
            # If not, try to join.
            # Ideally we'd use Flask's static path, but we are in a plugin.
            # Using os.path.abspath allows us to check existence.
            
            # Simple fix: If file doesn't exist, remove the tag to prevent htmldocx crash
            # or try to map it if we know where strict assets are.
            
            potential_path = Path(src).resolve()
            if not potential_path.exists():
                # Try relative to CWD
                potential_path = Path(os.getcwd()) / src.lstrip('/\\')
            
            if not potential_path.exists():
                # Log warning and remove image to prevent crash
                logger.warning(f"Word Export: Could not resolve image path '{src}'. Removing from export.")
                img.decompose()
            else:
                 # Update src to absolute path for htmldocx
                 img['src'] = str(potential_path)

    clean_html = str(soup)

    # Generate Word Doc
    doc = Document()
    new_parser = HtmlToDocx()
    
    try:
        new_parser.add_html_to_document(clean_html, doc)
    except Exception as e:
        logger.error(f"HtmlToDocx conversion failed (likely image issue): {e}")
        # Fallback: Try converting without images if that was the cause?
        # Or just re-raise properly wrapped
        # For now, we tried to clean images above. If it still fails, it's serious.
        # Let's add a text fallback to the doc if empty
        doc.add_paragraph(f"[Export Error: Document content could not be fully converted. Details: {e}]")

    # Post-processing (Bookmarks)
    heading_ids = {}
    if main_content:
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
             if heading.get('id'):
                 heading_ids[heading.get_text(strip=True)] = heading.get('id')
    
    for paragraph in doc.paragraphs:
        if paragraph.style.name.startswith('Heading') and paragraph.text.strip() in heading_ids:
            add_bookmark(paragraph, heading_ids[paragraph.text.strip()])

    # Post-processing (Styles - Table Grid)
    for table in doc.tables:
        table.style = 'Table Grid'
        # Basic header styling attempt
        if len(table.rows) > 0:
            for cell in table.rows[0].cells:
                shading_elm = OxmlElement('w:shd')
                shading_elm.set(qn('w:fill'), '6366f1')
                cell._element.get_or_add_tcPr().append(shading_elm)

    # Save to Buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    logger.info("Word export complete.")
    return buffer.getvalue()

# Expose features for FeatureManager
def get_features():
    # Helper to access injected classes safely
    # If not injected (e.g. static analysis), these might fail, which is expected.
    _Feature = globals().get('Feature')
    _FeatureType = globals().get('FeatureType')
    _FeatureState = globals().get('FeatureState')
    
    if not _Feature:
        logger.error("Plugin dependency injection failed: Feature class missing.")
        return []

    return [
        _Feature(
            name="docx",
            handler=export_to_word,
            feature_type=_FeatureType.EXPORT_HANDLER,
            state=_FeatureState.STANDARD
        )
    ]
