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

# Imports for SafeHtmlToDocx and export_to_word
try:
    from htmldocx import HtmlToDocx
    from docx import Document
    from docx.shared import RGBColor, Pt, Inches
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR
    import re
except ImportError as e:
    # Defer error handling to export_to_word if these are not available
    # This allows the module to load even if docx dependencies are missing
    HtmlToDocx = None
    Document = None
    RGBColor = None
    Pt = None
    OxmlElement = None
    qn = None
    WD_ALIGN_PARAGRAPH = None
    WD_COLOR = None
    re = None
    _word_export_import_error = e

class SafeHtmlToDocx(HtmlToDocx):
    """
    Subclass of HtmlToDocx to fix fragile color parsing that crashes on invalid hex/rgb strings.
    Overrides add_styles_to_run to add try/except blocks.
    """
    def add_styles_to_run(self, style):
        if 'color' in style:
            try:
                if 'rgb' in style['color']:
                    color = re.sub(r'[a-z()]+', '', style['color'])
                    parts = [x.strip() for x in color.split(',') if x.strip()]
                    if len(parts) >= 3:
                        colors = [int(p) for p in parts[:3]]
                        self.run.font.color.rgb = RGBColor(*colors)
                elif '#' in style['color']:
                    color = style['color'].strip().lstrip('#')
                    if len(color) == 3: color = ''.join([c*2 for c in color])
                    if len(color) >= 6:
                        colors = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                        self.run.font.color.rgb = RGBColor(*colors)
            except Exception: pass
            
        if 'background-color' in style:
            try:
                bg = style['background-color'].lower()
                # CriticMarkup Mapping
                if '#ffff00' in bg: self.run.font.highlight_color = WD_COLOR.YELLOW
                elif '#008000' in bg: self.run.font.highlight_color = WD_COLOR.BRIGHT_GREEN
                elif '#ff0000' in bg: self.run.font.highlight_color = WD_COLOR.RED
                else: pass
            except Exception: pass
            
        # Text Decoration (Strike/Underline) from styles
        if 'text-decoration' in style:
            if 'line-through' in style['text-decoration']:
                self.run.font.strike = True
            if 'underline' in style['text-decoration']:
                self.run.font.underline = True

        # Font Family Support (For Emojis)
        if 'font-family' in style:
            try:
                # Log font found
                # logger.info(f"Font Family Found: {style['font-family']}")
                fonts = style['font-family'].split(',')
                if fonts:
                    primary_font = fonts[0].strip().replace("'", "").replace('"', "")
                    self.run.font.name = primary_font
            except Exception: pass

    def add_styles_to_paragraph(self, style):
        # Override to support background-color (Shading) for Math Blocks
        super().add_styles_to_paragraph(style)
        
        if 'background-color' in style:
            try:
                color = style['background-color'].strip().lstrip('#')
                if len(color) == 3: color = ''.join([c*2 for c in color])
                if len(color) >= 6:
                    # Log finding color
                    # logger.info(f"Injecting Paragraph Shading: {color}")
                    pPr = self.paragraph._p.get_or_add_pPr()
                    shd = OxmlElement('w:shd')
                    shd.set(qn('w:val'), 'clear')
                    shd.set(qn('w:fill'), color)
                    
                    # Schema Order for pPr: ... pBdr, shd, tabs, spacing, ind, jc, rPr ...
                    successors = ['w:tabs', 'w:spacing', 'w:ind', 'w:jc', 'w:rPr']
                    target = None
                    for s in successors:
                        target = pPr.find(qn(s))
                        if target is not None:
                            break
                    
                    if target is not None:
                        pPr.insert_element_before(shd, target.tag)
                    else:
                        pPr.append(shd)
            except Exception as e:
                logger.error(f"Error injecting shading: {e}")


def transform_html_for_word(soup: BeautifulSoup):
    """
    Transforms HTML elements into Word-friendly structures.
    Modifies the soup in-place.
    """
    # 1. Transform Tabs (.tabbed-set) -> Vertical Headings + Content
    # Structure: .tabbed-set > input, label, .tabbed-content
    for tab_set in soup.find_all(class_='tabbed-set'):
        # Create a container for the flattened content
        flattened_div = soup.new_tag('div')
        
        # Iterate over labels and corresponding content
        labels = tab_set.find_all('label')
        # ... logic for tabs ...
        # (Assuming existing logic is fine, just referencing start)

    # 2. Transform Collapsible Details -> DIV with Bold Header
    for details in soup.find_all('details'):
        summary = details.find('summary')
        summary_text = summary.get_text().strip() if summary else "Details"
        
        container = soup.new_tag('div')
        container['style'] = "border: 1px solid #ccc; padding: 10px; margin: 10px 0; background-color: #f9f9f9;"
        
        header = soup.new_tag('p')
        header_b = soup.new_tag('strong')
        # Use a simpler arrow character for Word compatibility
        header_b.string = f"► {summary_text}"
        header.append(header_b)
        
        container.append(header)
        
        # Move content
        for child in list(details.contents):
            if child.name != 'summary':
                container.append(child)
                
        details.replace_with(container)

    # 3. Transform Emojis -> Colored Span (VS16)
    # Iterate text nodes to find emojis? No, standard emoji rendering usually relies on font.
    # If the user has raw emoji characters, we wrap them.
    # ... existing emoji logic ...

    # 4. Transform Math (KaTeX/MathJax) -> Clean TeX
    # Target: .katex-mathml annotation[encoding="application/x-tex"]
    # This is the Gold Standard for KaTeX fidelity.
    
    # First, handle KaTeX specific structure
    for katex_node in soup.find_all(class_='katex'):
        try:
            # Find the semantic annotation
            annotation = katex_node.find('annotation', attrs={'encoding': 'application/x-tex'})
            if annotation:
                tex_code = annotation.get_text().strip()
                
                # Check if it's display mode (block)
                # KaTeX usually has class 'katex-display' on a parent or 'display' attribute
                is_block = False
                parent = katex_node.parent
                if parent and 'katex-display' in (parent.get('class') or []):
                    is_block = True
                
                # Create replacement
                # We wrap in a code style so it stands out but is readable
                new_node = soup.new_tag('span')
                if is_block:
                    new_node.string = f"\n$$ {tex_code} $$\n"
                    new_node['style'] = "display: block; margin: 10px 0; font-family: 'Courier New', monospace; color: #333;"
                else:
                    new_node.string = f" ${tex_code}$ "
                    new_node['style'] = "font-family: 'Courier New', monospace; color: #333;"
                
                # If wrapped in .arithmatex, replace THAT container
                root_node = katex_node
                if parent and 'arithmatex' in (parent.get('class') or []):
                    root_node = parent
                elif parent and parent.name == 'span' and 'katex-display' in (parent.get('class') or []):
                     # Handle <span class="katex-display"><span class="katex">...</span></span>
                     # Check if *that* is in arithmatex
                     grandparent = parent.parent
                     if grandparent and 'arithmatex' in (grandparent.get('class') or []):
                         root_node = grandparent
                     else:
                         root_node = parent

                root_node.replace_with(new_node)
                continue
        except Exception as e:
            logger.warning(f"Failed to process KaTeX node: {e}")

    # Legacy MathJax Fallback
    for script in soup.find_all('script', type='math/tex'):
        tex = script.get_text()
        new_span = soup.new_tag('span')
        new_span.string = f"${tex}$"
        script.replace_with(new_span)
        
    # Remove Preview/Dummy spans
    for junk in soup.find_all(class_=['MathJax_Preview', 'katex-html']):
        junk.decompose()

        contents = tab_set.find_all(class_='tabbed-content')
        
        for i, label in enumerate(labels):
            if i < len(contents):
                # Create Heading from Label
                h4 = soup.new_tag('h4')
                h4.string = label.get_text(strip=True)
                h4['style'] = "margin-top: 12px; margin-bottom: 4px; color: #4b5563;"
                flattened_div.append(h4)
                
                # Append Content directly
                content = contents[i]
                # Remove class to prevent CSS interference if any
                del content['class']
                content['style'] = "margin-left: 8px; margin-bottom: 12px;"
                flattened_div.append(content)
        
        # Replace the complex tab set with the flattened div
        tab_set.replace_with(flattened_div)

    # 2. Transform Collapsible Details (details) -> Bold Summary + Content
    for details in soup.find_all('details'):
        summary = details.find('summary')
        if summary:
            # Create a bold paragraph for the summary
            p = soup.new_tag('p')
            b = soup.new_tag('b')
            b.string = f"▶ {summary.get_text(strip=True)}"
            p.append(b)
            p['style'] = "margin-top: 8px; margin-bottom: 4px;"
            
            # Insert summary P before the details tag
            details.insert_before(p)
            
            # Unwrap the details tag (keeping children, removing details wrapper)
            # The summary tag is still there, need to remove it
            summary.decompose()
            details.unwrap()

    # 3. Transform GitHub Alerts (.admonition) -> Single-Cell Tables
    # htmldocx doesn't support complex borders/backgrounds on divs well.
    alert_themes = {
        'note':      {'border': '#0969da', 'bg': '#e6f6ff', 'icon': 'ℹ️'},  # Blue
        'tip':       {'border': '#1a7f37', 'bg': '#dafbe1', 'icon': '💡'},  # Green
        'important': {'border': '#8250df', 'bg': '#f3e6ff', 'icon': '📣'},  # Purple
        'warning':   {'border': '#bf8700', 'bg': '#fff8c5', 'icon': '⚠️'},  # Amber (Fixed Hex)
        'caution':   {'border': '#d1242f', 'bg': '#ffebe9', 'icon': '🛑'},  # Red
        'danger':    {'border': '#d1242f', 'bg': '#ffebe9', 'icon': '⚡'}   # Red/Danger
    }
    
    for admonition in soup.find_all(class_='admonition'):
        # Determine type/color
        classes = admonition.get('class', [])
        color = '#0969da' # Default Blue
        bg_color = '#e6f6ff' # Default Light Blue
        icon = 'ℹ️'
        alert_type = 'NOTE'
        
        for cls, theme in alert_themes.items():
            if cls in classes:
                color = theme['border']
                bg_color = theme['bg']
                icon = theme['icon']
                alert_type = cls.upper()
                break
        
        table = soup.new_tag('table')
        # Add marker class so we can skip global table styling later
        table['class'] = 'docnexus-alert-table'
        # Use full border as htmldocx/Word support for partial borders is flaky
        table['style'] = f"border-collapse: collapse; width: 100%; border: 2px solid {color}; background-color: {bg_color};"
        tr = soup.new_tag('tr')
        td = soup.new_tag('td')
        td['style'] = f"padding: 8px; background-color: {bg_color};" # Apply BG to TD as well for safety
        
        # Extract Title
        title = admonition.find(class_='admonition-title')
        if title:
            # Create a bold paragraph for the title
            title_p = soup.new_tag('p')
            title_b = soup.new_tag('b')
            title_span = soup.new_tag('span')
            
            title_text = title.get_text(strip=True) or alert_type
            title_span.string = f"{icon} {title_text}"
            
            # Force Emoji Font for color rendering (applied to span, as b tag styles might be ignored)
            # Simplify font string to avoid parsing issues with quotes/commas
            title_span['style'] = f"color: {color}; font-family: Segoe UI Emoji;"
            
            title_b.append(title_span)
            title_p.append(title_b)
            td.append(title_p)
            title.decompose()
        
        # Move remaining content to TD
        # We need to copy children one by one to avoid issues while modifying the tree
        # td.append(title_p) # This line is a duplicate from the snippet, removed.
            
        # Move content to cell
        content_div = soup.new_tag('div')
        # Move siblings of title to content_div? No, GitHub Alerts flat structure is tricky.
        # Usually alert content follows the Title blockquote or similar.
        # But here we are assuming the whole 'alert' div content is what we want.
        # We already decomposed title, so the rest is content.
        for child in list(admonition.contents):
            content_div.append(child)
            
        td.append(content_div)
        tr.append(td)
        table.append(tr)
        admonition.replace_with(table)

    # 4. Transform Details (Collapsible) -> Styled Block
    # <details><summary>Title</summary>Content</details>
    for details in soup.find_all('details'):
        summary = details.find('summary')
        
        # Create container div
        container = soup.new_tag('div')
        container['style'] = "border: 1px solid #cccccc; padding: 10px; margin: 10px 0; background-color: #fafafa;"
        
        # Handle Title
        title_p = soup.new_tag('p')
        title_b = soup.new_tag('b')
        if summary:
            # Add icon and text
            title_b.string = f"▶ {summary.get_text(strip=True)}"
            summary.decompose() # Remove summary from details content
        else:
            title_b.string = "▶ Details"
        
        title_p.append(title_b)
        container.append(title_p)
        
        # Handle Content (Remaining children of details)
        content_div = soup.new_tag('div')
        content_div['style'] = "margin-top: 5px; margin-left: 15px;"
        
        # Move remaining contents
        for child in list(details.contents):
             content_div.append(child)
             
        container.append(content_div)
        details.replace_with(container)

    # 5. Transform Emojis (Wrap in Font Span)
    # Walk text nodes to find emojis and wrap them
    import re
    # Regex for common emojis (including supplementary pairs)
    # Simplified regex for the requested ones + ranges
    emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\u2600-\u26FF\u2700-\u27BF]')
    
    # We iterate a list of text nodes to modify them safely
    for text_node in soup.find_all(string=True):
        if text_node.parent and text_node.parent.name in ['script', 'style']:
            continue
            
        if emoji_pattern.search(text_node):
            # If emoji found, we need to split and wrap
            new_content = []
            last_idx = 0
            for match in emoji_pattern.finditer(text_node):
                start, end = match.span()
                # Text before
                if start > last_idx:
                    new_content.append(soup.new_string(text_node[last_idx:start]))
                
                # Emoji Wrapped
                emoji_span = soup.new_tag('span')
                # Append VS16 (\ufe0f) to force Emoji Presentation
                emoji_char = text_node[start:end]
                if not emoji_char.endswith('\ufe0f'):
                     emoji_char += '\ufe0f'
                
                emoji_span['style'] = "font-family: 'Segoe UI Emoji', sans-serif;"
                emoji_span.string = emoji_char
                new_content.append(emoji_span)
                
                last_idx = end
            
            # Text after
            if last_idx < len(text_node):
                new_content.append(soup.new_string(text_node[last_idx:]))
            
            # Replace text node with new structure
            # We use a span as a container if parent allows, or insert sibling
            # replace_with allows passing multiple arguments!
            text_node.replace_with(*new_content)

    # 6. Transform Task Lists -> Text [x] / [ ]
    for checkbox in soup.find_all('input', {'type': 'checkbox'}):
        is_checked = checkbox.has_attr('checked')
        replacement = soup.new_tag('span')
        replacement.string = "[x] " if is_checked else "[ ] "
        replacement['style'] = "font-family: monospace;"
        checkbox.replace_with(replacement)
        
    # 5. Transform CriticMarkup (Legacy numbering, keeping order)
    # Highlight
    for mark in soup.find_all('mark'):
        mark.name = 'span'
        # Yellow background for Word (will be mapped in add_styles_to_run override)
        mark['style'] = "background-color: #ffff00;"
        
    # Insert (Underline)
    for ins in soup.find_all('ins'):
        ins.name = 'span'
        ins['style'] = "color: #008000; text-decoration: underline;" # Green text + underline
        
    # Delete (Strikethrough)
    for delete in soup.find_all('del'):
        delete.name = 'span'
        delete['style'] = "color: #ff0000; text-decoration: line-through;" # Red text + strike

    # 6. Transform Definition Lists (dl, dt, dd) -> Bold + Indent
    for dl in soup.find_all('dl'):
        # We unwrap the dl, and style dt/dd
        for dt in dl.find_all('dt'):
            dt.name = 'p'
            b = soup.new_tag('b')
            b.string = dt.get_text(strip=True)
            dt.string = ''
            dt.append(b)
            dt['style'] = "margin-top: 8px; margin-bottom: 2px;"
            
        for dd in dl.find_all('dd'):
            dd.name = 'p'
            dd['style'] = "margin-left: 20px; margin-bottom: 8px;"
            
        dl.unwrap()

    # 7. Transform Math (.katex / .arithmatex) -> Code Block
    # 7a. Block Math
    # Arithmatex generic output uses class="arithmatex" and \[ ... \]
    for display_math in soup.find_all(class_='arithmatex'):
        # Check if it's block math (usually has \[ ... \])
            # Clean TeX: Robust extraction
            # 1. Check for script tag (MathJax non-generic)
            script_tex = display_math.find('script', type='math/tex')
            if script_tex:
                clean_tex = script_tex.get_text(strip=True)
            else:
                # 2. Generic Mode: Remove accessible/preview garbage
                # Remove MathJax_Preview if present
                for preview in display_math.find_all(class_='MathJax_Preview'):
                    preview.decompose()
                
                text = display_math.get_text(strip=True)
                # Try Regex for delimiters
                import re
                match = re.search(r'\\\[(.*?)\\\]', text, re.DOTALL)
                if match:
                    clean_tex = match.group(1).strip()
                else:
                    # Fallback: remove delimiters manually if regex fails but structure implies standard generic
                    clean_tex = text.replace(r'\[', '').replace(r'\]', '').strip()
            
            # Create Block
            code_p = soup.new_tag('p')
            code_p['style'] = "background-color: #f0f0f0; padding: 8px; border: 1px solid #ccc; margin: 10px 0;"
            
            # Word needs the FONT style on the run (span), not the paragraph (p)
            code_span = soup.new_tag('span')
            code_span['style'] = "font-family: 'Courier New', monospace;"
            code_span.string = clean_tex
            
            code_p.append(code_span)
            display_math.replace_with(code_p)

    # 7b. Inline Math (.katex) -> Inline Code Span
    for katex_span in soup.find_all(class_='katex'):
        # Skip if we just processed it inside a display block (orphaned check)
        if katex_span.find_parent(class_='katex-display'):
             continue
             
        # Try to find annotation or script
        annotation = katex_span.find('annotation', {'encoding': 'application/x-tex'})
        if annotation:
            tex_source = annotation.get_text(strip=True)
        else:
            # Fallback for inline
            tex_source = katex_span.get_text(strip=True)
        
        # Create Inline Span
        code_span = soup.new_tag('span')
        code_span['style'] = "font-family: monospace; background-color: #f0f0f0;"
        code_span.string = f" {tex_source} "
        
        katex_span.replace_with(code_span)



def export_to_word(html_content: str) -> bytes:
    """
    Exports HTML content to a Word (.docx) file byte stream.
    """
    if HtmlToDocx is None:
        logger.error(f"Failed to import Word export dependencies: {_word_export_import_error}")
        raise RuntimeError("Word export dependencies (htmldocx, python-docx) not installed.")

    # Size Check
    html_size = len(html_content.encode('utf-8'))
    if html_size > MAX_EXPORT_HTML_SIZE:
        raise ValueError(f"Content too large ({html_size/1024/1024:.2f} MB). Max {MAX_EXPORT_HTML_SIZE/1024/1024} MB.")

    logger.info(f"WordExport: Generating document from {html_size} bytes of HTML...")

    # Pre-process HTML with BeautifulSoup
    try:
        soup = BeautifulSoup(html_content, 'lxml')
    except:
        soup = BeautifulSoup(html_content, 'html.parser')
    
    # Cleaning (Scripts, Styles, Nav)
    for tag in soup.find_all(['script', 'style', 'nav']):
        tag.decompose()
        
    # Transform Complex HTML for Word Compatibility
    # (Tabs, Alerts, Details, Math, etc.)
    transform_html_for_word(soup)
    
    # Main Content Extraction
    # We want to include the Table of Contents (.toc-container) AND the Markdown Content (.markdown-content)
    # The frontend wraps both in #documentContent div (Line 729 view.html)
    # But usually sending full <html>.
    
    container = soup.find(id='documentContent')
    selected_content = []
    
    if container:
        # Extract TOC if present
        toc = container.find(class_='toc-container')
        if toc:
             # Style TOC for Word
            toc_header = toc.find(class_='toc-header')
            if toc_header:
                toc_header.name = 'h2' # Make it a standard header for Word
                toc_header['style'] = 'font-size: 14pt; color: #4b5563; margin-top: 0;'
            
            selected_content.append(toc)
            
            # Robust Page Break: Inject a unique marker we can find and replace with a REAL Word Break later
            # CSS page-break-after is unreliable in htmldocx
            pb_marker = soup.new_tag('p')
            pb_marker.string = "<<<DOCNEXUS_PAGE_BREAK>>>"
            selected_content.append(pb_marker)
            
        # Extract Markdown Content
        md_content = container.find(class_='markdown-content')
        if md_content:
             selected_content.append(md_content)
    else:
        # Fallback to old behavior if ID not found
        md_content = soup.find(class_='markdown-content')
        if md_content:
             selected_content.append(md_content)

    if selected_content:
        logger.info(f"WordExport: Analyzing {len(selected_content)} content parts for tables.")

        # Style Tables for Word (Apply to all tables in selected content)
        for part in selected_content:
            for table in part.find_all('table'):
                # 1. Logging & Classification
                classes = table.get('class', [])
                # Normalize class attribute to list (bs4 can return str or list)
                class_list = classes if isinstance(classes, list) else classes.split() if isinstance(classes, str) else []
                
                is_alert = 'docnexus-alert-table' in class_list
                
                # 2. Logic
                if is_alert:
                    logger.info(f"WordExport: Skipping Global Style for Alert Table. Classes={class_list}")
                    continue
                
                # Standard Table Styling
                # logger.debug(f"WordExport: Applying Global Style to Standard Table. Classes={class_list}")
                table['style'] = 'border-collapse: collapse; width: 100%; border: 2px solid #6366f1; margin-bottom: 20px;'
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
                
                # Colors and Styles injection
                for th in table.find_all('th'):
                    th['bgcolor'] = '#6366f1'
                    th['style'] = 'background-color: #6366f1 !important; color: #ffffff !important;'
                
                for td in table.find_all('td'):
                    td['style'] = 'padding: 8px; border: 1px solid #e5e7eb;'

        # Combine content
        combined_html = "".join([str(tag) for tag in selected_content])
        clean_html = f'<html><head><meta charset="utf-8"></head><body>{combined_html}</body></html>'
        
        # Capture main_content for booking logic later (use md_content reference)
        main_content = md_content if 'md_content' in locals() and md_content else None
    else:
        logger.warning("WordExport: No 'selected_content' found to style! using absolute fallback.")
        # Absolute fallback
        clean_html = f'<html><body>{soup.body.decode_contents() if soup.body else str(soup)}</body></html>'
        main_content = None

    # Pre-process HTML to resolve/fetch images (crucial for stability)
    # This prevents htmldocx from crashing on network errors or missing files.
    soup = BeautifulSoup(clean_html, 'html.parser')
    
    # We need a temp dir for downloaded images that persists during conversion
    import tempfile
    import urllib.request
    from urllib.parse import urlparse
    import shutil
    
    # Create a temporary directory for this export session
    with tempfile.TemporaryDirectory() as temp_img_dir:
        temp_dir_path = Path(temp_img_dir)
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
                
            is_external = src.startswith(('http://', 'https://'))
            new_src = None
            
            try:
                if is_external:
                    # Check for SVG in URL before downloading to save time
                    path_obj = Path(urlparse(src).path)
                    if path_obj.suffix.lower() == '.svg':
                         raise ValueError("SVG format is not supported by Word.")

                    # Attempt to download external image using standard library
                    req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=3.0) as response:
                        # Check Content-Type for SVG
                        ctype = response.info().get_content_type().lower()
                        if 'svg' in ctype:
                             raise ValueError("SVG format is not supported by Word.")

                        # Determine filename
                        filename = path_obj.name or "image.png"
                        local_path = temp_dir_path / filename
                        
                        with open(local_path, 'wb') as f:
                            shutil.copyfileobj(response, f)
                    
                    new_src = str(local_path)
                    
                elif src.startswith('data:image/'):
                    # Handle Data URIs (e.g. Mermaid Exports)
                    import base64
                    try:
                        from PIL import Image
                    except ImportError:
                        Image = None
                    
                    if ';base64,' in src:
                        header, data = src.split(';base64,')
                        ctype = header.split(':')[1]
                        
                        if 'svg' in ctype:
                             raise ValueError("SVG data URIs are not supported.")
                        
                        img_data = base64.b64decode(data)
                        
                        # Process Image (Flatten Transparency)
                        if Image:
                            try:
                                with Image.open(io.BytesIO(img_data)) as im:
                                   # Convert to RGBA if strictly RGB to ensure consistent handling (though usually PNG is RGBA)
                                   if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                                       # Create white background
                                       bg = Image.new('RGB', im.size, (255, 255, 255))
                                       # Paste image on top using alpha channel
                                       if im.mode != 'RGBA':
                                           im = im.convert('RGBA')
                                       bg.paste(im, mask=im.split()[3]) # 3 is the alpha channel
                                       
                                       # Save flattened image
                                       output = io.BytesIO()
                                       bg.save(output, format='PNG')
                                       img_data = output.getvalue()
                                       ext = '.png'
                                   else:
                                        ext = '.png' if 'png' in ctype else '.jpg'
                            except Exception as iconv_err:
                                logger.warning(f"PIL Conversion failed, using original data: {iconv_err}")
                                ext = '.png' if 'png' in ctype else '.jpg'
                        else:
                            ext = '.png' if 'png' in ctype else '.jpg'

                        filename = f"embedded_image_{hash(data)}{ext}"
                        local_path = temp_dir_path / filename
                        
                        with open(local_path, 'wb') as f:
                            f.write(img_data)
                            
                        new_src = str(local_path)
                    else:
                        raise ValueError("Unsupported Data URI format")

                elif not src.startswith('data:'):
                     # Resolve local path
                     # Try relative to CWD first
                    potential_path = Path(src).resolve()
                    if not potential_path.exists():
                        # Try relative to server root if CWD failed
                        potential_path = (Path(os.getcwd()) / src.lstrip('/\\')).resolve()
                    
                    if potential_path.exists():
                        if potential_path.suffix.lower() == '.svg':
                             raise ValueError("SVG format is not supported.")
                        new_src = str(potential_path)
                    else:
                        logger.warning(f"Word Export: Local image not found: {src}")

                # Update src if valid path found
                if new_src:
                    img['src'] = new_src
                else:
                    raise ValueError("Could not resolve image source.")

            except Exception as e:
                # logger.warning(f"Word Export: Skipping image '{src}': {e}")
                # Fallback to alt text
                # Fallback to alt text
                alt_text = img.get('alt', '')
                replacement = soup.new_tag('span')
                # Remove brackets. If it's an emoji (detected by regex or length), we might want normal font.
                # But for safety, keep the fallback text as is, just without brackets.
                replacement.string = alt_text if alt_text else "Image"
                
                # If it looks like an emoji (short length), style it as emoji font
                if len(alt_text) <= 2:
                     replacement['style'] = "font-family: 'Segoe UI Emoji', sans-serif;"
                else:
                     replacement['style'] = "color: #666; font-style: italic; border: 1px solid #ccc; padding: 2px;"
                
                img.replace_with(replacement)

        # Sanitize Styles to prevent htmldocx crashes (invalid literal for int() with base 16)
        # htmldocx chokes on 'stroke: none', 'fill: ...', and 'color: auto/none' often found in Mermaid/Shims
        for tag in soup.find_all(True):
            if tag.has_attr('style'):
                styles = [s.strip() for s in tag['style'].split(';') if s.strip()]
                clean_styles = []
                for s in styles:
                    if ':' in s:
                        prop, val = s.split(':', 1)
                        prop = prop.strip().lower()
                        val = val.strip().lower()
                        
                        # Strip dangerous SVG-related styles that htmldocx doesn't understand
                        if prop in ['stroke', 'stroke-width', 'fill', 'fill-opacity', 'stroke-opacity']:
                            continue
                            
                        # Strip unsupported values that cause htmldocx to crash (base 16 error)
                        # This includes 'transparent', 'currentColor', 'var(...)', 'inherit', empty strings, and 'rgb/rgba'
                        if any(x in val for x in ['transparent', 'currentcolor', 'var(', 'inherit', 'initial', 'unset', 'rgb', 'rgba']):
                             continue
                        
                        if not val: # Empty value
                             continue
                             
                        # Explicit check for keywords if they are the ONLY value (e.g. color: none)
                        if val in ['none', 'auto']:
                             continue
                        
                        # HEX Validation: If it looks like a hex color, it MUST be valid
                        # htmldocx crashes on '#' or invalid hex with int('', 16)
                        if '#' in val:
                            import re
                            # Check if the value is purely a hex code (allow for !important suffix which we don't prefer but might exist)
                            # We strip !important for the check
                            clean_val = val.replace('!important', '').strip()
                            if clean_val.startswith('#'):
                                # It's a hex color. Validate it.
                                if not re.match(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$', clean_val):
                                    # Invalid hex (e.g. '#', '#12', '#xyz')
                                    continue
 
                        clean_styles.append(s)
                
                if clean_styles:
                    tag['style'] = "; ".join(clean_styles)
                else:
                    del tag['style']
                    
        # Also remove 'stroke' and 'fill' attributes directly
        for tag in soup.find_all(attrs={"stroke": True}):
            del tag['stroke']
        for tag in soup.find_all(attrs={"fill": True}):
            del tag['fill']
        for tag in soup.find_all(attrs={"viewbox": True}):
             del tag['viewbox'] # Clean up any lingering SVG debris



        clean_html = str(soup)

        # Generate Word Doc
        doc = Document()
        new_parser = SafeHtmlToDocx()
        
        try:
            # Now safe to convert
            new_parser.add_html_to_document(clean_html, doc)
            
            # -------------------------------------------------------------------------
            # POST-PROCESSING: Apply Fidelity Styling directly to DOCX objects
            # This bypasses htmldocx limitations by acting on the final structure.
            # -------------------------------------------------------------------------
            
            # 1. Apply Alert Backgrounds (Table Shading)
            for table in doc.tables:
                try:
                    # heuristic: check first cell text for Alert Icons/Text
                    # Use 'in' logic instead of 'startswith' to handle variability in Icon unicode (VS16 etc)
                    if not table.rows or not table.columns: continue
                    
                    first_cell = table.cell(0, 0)
                    text = first_cell.text.strip()
                    
                    bg_color = None
                    if "Note" in text and ("ℹ" in text or "i" in text): # Handle ℹ️
                        bg_color = "e6f6ff" 
                    elif "Tip" in text and "💡" in text:
                        bg_color = "dafbe1"
                    elif "Important" in text and "📣" in text:
                        bg_color = "f3e6ff"
                    elif "Warning" in text and "⚠" in text: # Handle ⚠️ (U+26A0)
                        bg_color = "fff8c5"
                    elif ("Caution" in text or "Danger" in text) and ("🛑" in text or "⚡" in text):
                         bg_color = "ffebe9"
                         
                    if bg_color:
                        # Apply shading to the cell
                        tcPr = first_cell._tc.get_or_add_tcPr()
                        
                        # Remove existing shd if any
                        existing_shd = tcPr.find(qn('w:shd'))
                        if existing_shd is not None:
                            tcPr.remove(existing_shd)
                            
                        shd = OxmlElement('w:shd')
                        shd.set(qn('w:val'), 'clear')
                        shd.set(qn('w:fill'), bg_color)
                        
                        # Insert in correct schema order (after tcBorders, before noWrap/tcMar/vAlign etc)
                        # Failure to respect this causes Word to ignore the shading silently.
                        # Successors: noWrap, tcMar, textDirection, tcFitText, vAlign, hideMark
                        successors = ['w:noWrap', 'w:tcMar', 'w:textDirection', 'w:tcFitText', 'w:vAlign', 'w:hideMark']
                        target = None
                        for s in successors:
                            target = tcPr.find(qn(s))
                            if target is not None:
                                break
                                
                        if target is not None:
                            tcPr.insert_element_before(shd, target.tag)
                        else:
                            tcPr.append(shd)
                            
                        # Fix Icon Font (Segoe UI Emoji)
                        # Iterate runs in the first paragraph to find the icon
                        if first_cell.paragraphs:
                            for run in first_cell.paragraphs[0].runs:
                                # Heuristic: If run contains the icon character
                                if any(icon_char in run.text for icon_char in ["ℹ", "💡", "📣", "⚠️", "🛑", "⚡"]):
                                    run.font.name = 'Segoe UI Emoji'
                            
                        # Also fix borders if needed? 
                        # htmldocx usually handles borders if HTML had them.
                        
                except Exception as e:
                    logger.warning(f"WordExport: Failed to style table: {e}")

            # 2. Apply Math Styling (Paragraph Shading)
            # We identified Math blocks as code blocks. 
            # If they didn't get styled by add_styles_to_paragraph, we can catch them here.
            # But add_styles_to_paragraph IS strictly supported by SafeHtmlToDocx if called correctly.
            # We'll leave Math for now as the Post-Process Table fix is the big one.

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()

            logger.error(f"HtmlToDocx conversion failed: {e}", exc_info=True)
            doc.add_paragraph(f"[Export Error: Document content could not be fully converted.]")
            doc.add_paragraph(f"Details: {str(e)}")
            # Add traceback in small font for debugging
            p = doc.add_paragraph()
            run = p.add_run(error_details)
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor(128, 128, 128)

        # Post-processing (Bookmarks)
        heading_ids = {}
        if main_content:
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                 if heading.get('id'):
                     heading_ids[heading.get_text(strip=True)] = heading.get('id')
        
        for paragraph in doc.paragraphs:
            if paragraph.style.name.startswith('Heading') and paragraph.text.strip() in heading_ids:
                add_bookmark(paragraph, heading_ids[paragraph.text.strip()])

        # Post-processing (Hard Page Break Injection)
        # Search for our unique marker and replace with a native WD_BREAK_PAGE
        from docx.enum.text import WD_BREAK
        
        for i, p in enumerate(doc.paragraphs):
            if "<<<DOCNEXUS_PAGE_BREAK>>>" in p.text:
                # Clear the marker text
                p.clear()
                # Insert the Page Break
                run = p.add_run()
                run.add_break(WD_BREAK.PAGE)
                # Ensure no weird spacing/styles on this empty line
                p.style = doc.styles['Normal']
                continue

            # Smart Page Breaks (Keep with Next & Keep Together)
            # 1. Headings: Always keep with next paragraph
            if p.style.name.startswith('Heading'):
                p.paragraph_format.keep_with_next = True
            
            # 2. Code Blocks / Quotes: Try to keep them together on one page
            # htmldocx maps <pre> to 'No Spacing' or paragraphs with specific fonts usually?
            # It's inconsistent, but we can try to detect if it LOOKS like code (Courier New, Consolas, or shaded background)
            # A safer generic heuristic: If it has a border or shading (which we applied to tables/code earlier?), keep it together.
            # But paragraphs don't easily expose borders in python-docx API without diving into XML.
            
            # Simple fallback: If style involves 'Code', 'Quote', 'Intense Quote'
            if any(s in p.style.name for s in ['Code', 'Quote', 'Macro']):
                p.paragraph_format.keep_together = True

        # Post-processing (Image Sizing & Centering)
        # Fixes oversized diagrams in Word export
        try:
            # Calculate writable limits
            section = doc.sections[0]
            page_width = section.page_width
            page_height = section.page_height
            margin_x = section.left_margin + section.right_margin
            margin_y = section.top_margin + section.bottom_margin
            
            writable_width = page_width - margin_x
            writable_height = page_height - margin_y
            
            from docx.shared import Emu

            for shape in doc.inline_shapes:
                # Calculate aspect ratio
                if shape.width == 0: continue
                aspect_ratio = shape.height / shape.width
                
                # 1. Width Constraint
                if shape.width > writable_width:
                    shape.width = writable_width
                    shape.height = int(writable_width * aspect_ratio)
                
                # 2. Height Constraint (Applied after width to ensure final fit)
                if shape.height > writable_height:
                    shape.height = writable_height
                    shape.width = int(writable_height / aspect_ratio)
                
                # Force Center Alignment for paragraphs containing images
                # This works because htmldocx usually puts block images in their own p (or we forced it)
                # We check if the paragraph is mostly just this image to avoid centering mixed content
                # For now, simplistic approach: if paragraph has an inline shape, center it.
                # Accessing the parent paragraph of a shape isn't direct in python-docx public API,
                # but we can try iterating paragraphs and finding runs with drawings.
                pass 
            
            # Robust Centering Loop
            # Iterate paragraphs, find those with images, force center
            for p in doc.paragraphs:
                # Check for blip/drawing
                if 'Graphic' in p._element.xml or 'drawing' in p._element.xml:
                    # Heuristic: mostly image content?
                    if len(p.text.strip()) < 5:  # Almost no text, valid assumption for a diagram block
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        
        except Exception as e:
            logger.warning(f"Failed to resize images: {e}")

        # Post-processing (Style Table Grid)
        for table in doc.tables:
            # Skip Alerts (Heuristic)
            if table.rows and table.columns:
                 first_text = table.cell(0,0).text.strip()
                 # Reuse the robust matching logic or just check for our specific markers
                 if ("Note" in first_text and ("ℹ" in first_text or "i" in first_text)) or \
                    ("Tip" in first_text and "💡" in first_text) or \
                    ("Important" in first_text and "📣" in first_text) or \
                    ("Warning" in first_text and "⚠" in first_text) or \
                    (("Caution" in first_text or "Danger" in first_text) and ("🛑" in first_text or "⚡" in first_text)):
                     continue

            table.style = 'Table Grid'
            if len(table.rows) > 0:
                for cell in table.rows[0].cells:
                    # Check if cell has explicit shading already (from our Alert logic or otherwise)
                    # Use existing tcPr to check for w:shd
                    tcPr = cell._element.get_or_add_tcPr()
                    if tcPr.find(qn('w:shd')) is not None:
                        continue
                        
                    shading_elm = OxmlElement('w:shd')
                    shading_elm.set(qn('w:fill'), '6366f1')
                    tcPr.append(shading_elm)

        # Post-processing (Fix Internal Hyperlinks for TOC)
        # htmldocx creates external links for #anchors. We need to convert them to w:anchor.
        try:
            part = doc.part
            rels = part.rels
            
            # Iterate all paragraphs to find hyperlinks
            for p in doc.paragraphs:
                for child in p._element:
                    if child.tag.endswith('hyperlink'):
                        rid = child.get(qn('r:id'))
                        if rid and rid in rels:
                            rel = rels[rid]
                            if rel.target_ref and rel.target_ref.startswith('#'):
                                # Found internal link candidate
                                anchor_name = rel.target_ref[1:] # strip #
                                
                                # Convert to internal anchor
                                # Note: We assume the bookmark name matches the ID (which we ensured in our bookmarking logic? 
                                # Actually our bookmark logic uses get_text()??
                                # NO. 
                                # Line 233: heading_ids[heading.get_text()] = heading.get('id')
                                # Line 237: add_bookmark(..., heading_ids[...]) -> creates bookmark with NAME = ID.
                                # So if href="#id", and bookmark name="id", it works.
                                
                                child.set(qn('w:anchor'), anchor_name)
                                # Remove r:id (external reference)
                                try:
                                    del child.attrib[qn('r:id')]
                                except:
                                    pass
                                child.set(qn('w:history'), '1')
        except Exception as e:
            logger.warning(f"Failed to fix internal hyperlinks: {e}")

        # Save to Buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
    # Context exits, temp dir deleted.
    # Context exits, temp dir deleted.
    logger.info("WordExport: Complete. Returning bytes.")
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

# Metadata
PLUGIN_METADATA = {
    'name': 'Word Export',
    'description': 'Exports documentation to Microsoft Word (.docx) with TOC and styles.',
    'category': 'export',
    'icon': 'fa-file-word',
    'preinstalled': True
}
