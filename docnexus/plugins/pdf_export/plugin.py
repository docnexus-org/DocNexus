import os
import sys
import logging
import traceback
import re
from pathlib import Path
from bs4 import BeautifulSoup, Tag

PLUGIN_DIR = Path(__file__).parent
ENABLED_FILE = PLUGIN_DIR / "ENABLED"
DEPENDENCIES = ["xhtml2pdf"]

import io
import urllib.parse
import requests
import base64

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# PDF Transformation Logic
# -------------------------------------------------------------------------

def parse_tex_to_html(soup_factory, tex_str):
    """
    Converts simple TeX (subscripts, superscripts, basic symbols) to an HTML span.
    Handles: x^2, x_i, x_{i+1}, \alpha -> alpha
    """
    container = soup_factory.new_tag('span')
    # PDF Fonts: DejaVu Sans or standard sans/serif usually works best with xhtml2pdf
    container['style'] = "font-family: 'Times New Roman', serif;" 
    
    cursor = 0
    n = len(tex_str)
    
    while cursor < n:
        char = tex_str[cursor]
        
        if char in ('^', '_'):
            tag_name = 'sup' if char == '^' else 'sub'
            cursor += 1
            content = ""
            
            # Check for Group { }
            if cursor < n and tex_str[cursor] == '{':
                cursor += 1
                nesting = 1
                start_grp = cursor
                while cursor < n and nesting > 0:
                    if tex_str[cursor] == '{': nesting += 1
                    elif tex_str[cursor] == '}': nesting -= 1
                    if nesting > 0: cursor += 1
                    
                content = tex_str[start_grp:cursor]
                cursor += 1 # Skip closing }
            elif cursor < n:
                # Single char argument
                if tex_str[cursor] == '\\':
                        # Extract macro
                        macro_start = cursor
                        cursor += 1
                        while cursor < n and tex_str[cursor].isalpha():
                            cursor += 1
                        content = tex_str[macro_start:cursor]
                else:
                    content = tex_str[cursor]
                    cursor += 1
                    
            elem = soup_factory.new_tag(tag_name)
            # Recursively parse content
            if '^' in content or '_' in content:
                # Recursive call
                nested_span = parse_tex_to_html(soup_factory, content)
                for child in list(nested_span.contents):
                    elem.append(child)
            else:
                key = content.replace('\\', '').strip()
                symbols = {
                    'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'theta': 'θ', 'pi': 'π', 
                    'sigma': 'σ', 'omega': 'ω', 'Delta': 'Δ', 'mu': 'μ', 'lambda': 'λ',
                    'infty': '∞', 'rightarrow': '→', 'leftarrow': '←', 'approx': '≈',
                    'neq': '≠', 'le': '≤', 'ge': '≥', 'times': '×', 'cdot': '·'
                }
                elem.string = symbols.get(key, content.replace('\\', ''))
            
            container.append(elem)
            
        elif char == '{' or char == '}':
                cursor += 1
        elif char == '\\':
            macro_start = cursor
            cursor += 1
            while cursor < n and tex_str[cursor].isalpha():
                cursor += 1
            macro = tex_str[macro_start+1:cursor]
            
            symbols = {
                'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'theta': 'θ', 'pi': 'π',
                'sigma': 'σ', 'omega': 'ω', 'Delta': 'Δ', 'mu': 'μ', 'lambda': 'λ',
                'infty': '∞', 'rightarrow': '→', 'leftarrow': '←', 'approx': '≈',
                    'neq': '≠', 'le': '≤', 'ge': '≥', 'times': '×', 'cdot': '·', 'frac': ''
            }
            
            if macro == 'frac':
                    pass
            else:
                container.append(soup_factory.new_string(symbols.get(macro, "")))
        else:
            text_buffer = ""
            while cursor < n and tex_str[cursor] not in ('^', '_', '{', '}', '\\'):
                text_buffer += tex_str[cursor]
                cursor += 1
            container.append(soup_factory.new_string(text_buffer))
            
    return container

def transform_html_for_pdf(soup: BeautifulSoup):
    """
    Transforms HTML elements into PDF-friendly structures.
    Modifies the soup in-place.
    """
    import traceback
    # helper for creating new tags reliably (BS4 Tag objects sometimes lack new_tag in older versions)
    factory_soup = BeautifulSoup("", 'html.parser')

    try:
        # 1. Remove Header Permalinks (Double Square Artifacts)
        for permalink in soup.find_all('a', class_='headerlink'):
            if permalink: permalink.decompose()

        # 2. Fix Internal Links (TOC & Anchors) & WikiLinks
        for element in soup.find_all(id=True):
            if not isinstance(element, Tag): continue
            if not element.find('a', attrs={'name': element['id']}):
                anchor_name = element['id']
                # Robust new_tag creation handling potential NoneType or missing method
                if hasattr(soup, 'new_tag') and callable(soup.new_tag):
                    new_anchor = soup.new_tag('a')
                else:
                    # Fallback: create fresh tag via new soup
                    new_anchor = BeautifulSoup("<a></a>", "html.parser").a.extract()
                
                new_anchor['name'] = anchor_name
                element.insert(0, new_anchor)

        # Fix WikiLinks / Internal Hrefs
        # Strategy:
        # 1. If it links to an ID present in the doc (TOC), use it.
        # 2. If it links to another file, `xhtml2pdf` cannot natively handle it unless we make it an absolute URL or merge docs.
        #    For now, we render it as an absolute URL if 'base_url' suggests it, or keep it as text to avoid broken links.
        #    But User explicitly complained it's "not clickable". 
        #    We will try to preserve it as a link if it looks like a URL path, or convert to a visual span if simpler.
        
        # Collect all valid anchor names in the doc for validation
        existing_anchors = set()
        for tag in soup.find_all(attrs={'name': True}):
            existing_anchors.add(tag['name'])
        for tag in soup.find_all(id=True):
            existing_anchors.add(tag['id'])

        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip existing valid protocols
            if href.startswith(('http:', 'https:', 'mailto:', 'data:', 'ftp:')):
                continue
                
            # Internal Hash Links
            if href.startswith('#'):
                # Valid internal link, keep it.
                continue
            
            # Application Links (WikiLinks usually come out as relative or /file/...)
            # If it matches an internal anchor (slug), link it.
            slug = href.strip('/').replace('.md', '').replace('file/', '')
            
            if slug in existing_anchors:
                link['href'] = f"#{slug}"
                continue
            
            # If it's a file link that doesn't exist as an anchor, we can't link to it in a solitary PDF.
            # We will convert it to an absolute link assuming localhost for now (or just text).
            # But making it "clickable" implies it should go SOMEWHERE.
            # Let's try to assume relative path is valid for PDF viewer if file exists? 
            # No, `xhtml2pdf` is converting HTML to PDF. File links are relative to CWD.
            # Best effort: Convert to Styled Text to indicate it's a reference but not broken.
            # OR, if User insists, we can make it a dead link style.
            # User expectation: "not have clickable link".
            # I will ensure it has `color: blue` and `text-decoration: underline` explicitly via style,
            # AND I will prepend `http://localhost:5000/` (or similar) to make it opening the web view?
            # Safe approach: text-decoration.
            
            # Check if it looks like a WikiLink
            if 'wikilink' in (link.get('class') or []) or not '.' in href:
                 # Force styling for visibility
                 link['style'] = f"color: #0969da; text-decoration: underline; {link.get('style', '')}"
                 # We simply leave the href alone? No, xhtml2pdf might complain.
                 # Let's make it a valid external link to a placeholder DB or similar? 
                 # Actually, let's just leave it if it's not empty, but ensure style is applied.
                 pass

        # Inject CSS for Emojis and Alerts
        # Emojis need careful sizing to avoid being "weirdly large" or clipped.
        # vertical-align: middle usually balances them better than baseline with a negative offset.
        style_tag = factory_soup.new_tag('style')
        style_tag.string = """
            .emoji {
                font-family: 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif;
                font-size: 1.0em; /* Reset boost */
                vertical-align: middle;
                line-height: 1.5; /* Increase space to prevent clipping */
                padding: 0 2px;
            }
        """
        if soup.head:
            soup.head.append(style_tag)
        else:
            soup.append(style_tag)

        # 3. Transform Tabs (.tabbed-set) -> Vertical Headings + Content
        for tab_set in soup.find_all(class_='tabbed-set'):
            if not isinstance(tab_set, Tag): continue
            
            flattened_div = factory_soup.new_tag('div')
            labels = tab_set.find_all('label')
            contents = tab_set.find_all(class_='tabbed-content')
            
            for i, label in enumerate(labels):
                label_text = label.get_text().strip()
                header = factory_soup.new_tag('h4')
                header.string = label_text
                header['style'] = "margin-top: 15px; margin-bottom: 5px; color: #555; border-bottom: 1px solid #eee;"
                flattened_div.append(header)
                if i < len(contents):
                    flattened_div.append(contents[i])
            
            tab_set.replace_with(flattened_div)

        # 3.5 Abbreviation Handling (First-Use Expansion)
        # Standard Print practice: Expand "Abbr (Definition)" on first use, then just "Abbr".
        seen_abbrs = set()
        for abbr in soup.find_all('abbr'):
            title = abbr.get('title')
            text = abbr.get_text().strip()
            
            if title and text:
                key = (text, title)
                if key not in seen_abbrs:
                    # First time seeing this abbreviation: Expand it
                    # We create a span to hold "Text (Title)"
                    new_content = f"{text} ({title})"
                    abbr.string = new_content
                    # Mark as seen
                    seen_abbrs.add(key)
                else:
                     # Subsequent use: Just styling (handled by CSS)
                     pass

        # 3.6 Task List / Checklist Handling
        # Convert <input type="checkbox"> into visual icons (☑ / ☐) via our Emoji renderer for consistency.
        # This replaces the native input which xhtml2pdf renders poorly or not at all (static).
        task_items = soup.find_all('li', class_='task-list-item')
        if task_items:
            print(f"DEBUG: Found {len(task_items)} task list items to transform.")
            
        for li in task_items:
            # Find the input
            checkbox = li.find('input', type='checkbox')
            if not checkbox:
                continue
                
            is_checked = checkbox.has_attr('checked')
            
            # Use standard unicode chars for checkbox state, but Render them as Emojis/Images for quality
            # checked: 2611 (☑), unchecked: 2610 (☐)
            # Or use emoji style: ✅ (2705) vs ⬜ (2B1C)
            # Let's stick to the Classic Ballot Box which looks like a form control.
            char = '\u2611' if is_checked else '\u2610'
            
            # Use our existing base64 generation if available (requires moving that function UP or importing)
            # The function `get_emoji_base64` is defined inside `transform_html_for_pdf` but further down.
            # We need to move `get_emoji_base64` definition to the TOP of `transform_html_for_pdf` or outer scope.
            # For now, to avoid massive refactor, I will instantiate strict Base64 icons here directly 
            # OR I will rely on Text with a nice font if simpler, BUT User wants "Top Rated" look.
            # actually, `xhtml2pdf` likely handles the font `Segoe UI Emoji` if installed? No, it needs ttf load.
            # I will USE THE SAME LOGIC as Alerts - hardcoded Base64 for stability and strict visuals.
            
            # Icons from: https://icon-sets.iconify.design/ (Simple vector-like PNGs)
            # Unchecked (Gray Box)
            icon_unchecked = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABmJLR0QA/wD/AP+gvaeTAAAAUElEQVRoge3QwQnAIBQFQYO0/y5sQTAW82GhA1n4wcx8n/O+985yX2b23vN/5z3X+Z333Od/3vN6/vOe9/Of93yfv7zneb/znef9zvN+5/n/fQCjFw/i4V8FmAAAAABJRU5ErkJggg==" # Just a box border? No, this is empty.
            # Let's use simple data URIs for 16x16 bitmaps.
            
            # Better: Move basic emoji logic to top or just defer this loop?
            # I'll defer this loop to AFTER `get_emoji_base64` is defined (Section 5).
            # I will insert a "TODO helper" style comment here and actually place the code further down.
            pass 

        # 4. Transform Collapsible Details -> DIV with Bold Header
        for details in soup.find_all('details'):
            if not isinstance(details, Tag): continue
            
            summary = details.find('summary')
            summary_text = summary.get_text().strip() if summary else "Details"
            
            container = factory_soup.new_tag('div')
            container['style'] = "border: 1px solid #ccc; padding: 10px; margin: 10px 0; background-color: #f9f9f9;"
            
            header = factory_soup.new_tag('p')
            header_b = factory_soup.new_tag('strong')
            header_b.string = f"► {summary_text}"
            header.append(header_b)
            container.append(header)
            
            content_div = factory_soup.new_tag('div')
            # Safely move content
            if details.contents:
                for child in list(details.contents):
                    if child != summary:
                        content_div.append(child)
            
            container.append(content_div)
            details.replace_with(container)

        # 4.1. Enhance Definition Lists (Strong Terms + Indent)
        # xhtml2pdf may not bold <dt> by default, so we force specific styling/structure.
        for dt in soup.find_all('dt'):
            # Force Bold
            if not dt.find(['strong', 'b']):
                new_b = factory_soup.new_tag('strong')
                # Copy contents to new tag
                new_b.extend(list(dt.contents))
                dt.clear()
                dt.append(new_b)
                
            # Add inline style for ensured top margin
            dt['style'] = f"margin-top: 10px; margin-bottom: 2px; color: #222; {dt.get('style', '')}"
            
        for dd in soup.find_all('dd'):
            # Add inline style for indentation
            dd['style'] = f"margin-left: 20px; margin-bottom: 8px; color: #444; {dd.get('style', '')}"


        # 4.5. Enhance GitHub Alerts / Admonitions (Flattened for PDF Stability)
        # MOVED BEFORE EMOJI LOGIC so icons get processed if needed (though we wrap them manually).
        # FLATTENING STRATEGY:
        # xhtml2pdf renders tables with block content poorly (splits backgrounds).
        # We flatten the alert into a single <td> containing inline elements separated by <br>.
        
        # Renderer produces standard Admonition classes: .admonition .note, .admonition .tip etc.
        # We also keep support for markdown-alert just in case.
        
        alert_icons = {
            'note': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABgElEQVR4nO2bu03EQBRF7xxthEROBVSwrdAAGX3QAzExrRATkJHQANIGJEZCAlkr7/o3X989kgNb9nv3jt/Y45EndPIGmbPLmezq4X1ywR2eboMyELpKDJdqkNBVbjx1Q4SuAdMpG4NWzcfKG7oGjcesBrZgfo0eciZLzRJd5EiSk7n6SBm8FHN0kiJoDUzVS8xgtTFFNzGC1MyYftZc3ArnfCBz2PrdH/PDnJNbZ8gXMgeZE7pC5X+3v9bz/c3//v7xQ2+f39m/HJE5ODz8jun7RObsSiV+ef363UqDzMGt/x/7RebsSiUuOQ7og8xB5iBzkDnIHGQOMgeZQ+5/cmrhzy8yB5mDzKG/4/IcuEyKnusCh41XwbE/ZA4yh6GDW+0GQ76Yc3LLnPKDzAljc+FbmC4/V82subgFxvQTI0itTNFNzGA1MVUvKYKWZo5OUgYvwVx95EiSiyW6yJksJUv1hBgv+ZJjhbU3ghpElMwbLusGlQ7blaOnsFs7rAb4AedJsUM6zwafAAAAAElFTkSuQmCC',
            'tip': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAADsklEQVR4nO2ba0gUURiG3/lay2ubWbawUmFIYUJiZlT0x/JPRkIXQcMKC4SCflUE/siECroXlGB0U0FByiCKjEKy2xqBUmYXMbJaXIvKrKzU3Ykd2sktda/nzMxODwzMGc453/t+c2bOmWFGEKFvCDrHwDOYedd8rwecdXeTAA4IokoMK5UQQVS5cdaJEEQNmGaZDNKq+WDFFUQNGg/maKBQMB+IHuIZjDX+6CIeQXjiqz5i2blS+KKTWHSqBrzVS8HsTG14o5uC0Yma8aSfAmmsFUbzQdA5FOpn35Mf8qWy1hnOF0HnEHSOIHIc/jHjopCbmo3FiRmYbUpCbKQRJBA+9X1Gx4dOWDpbUNtyBW96usDryVHglYCC9JUoztoiJWE07A4Hapovo6T+KPr6v/NNgJmR+T3LtmFDxmqf2jx/9xJrzm/Gh289TJNgAGM2zs/9x/yFR9dQ9bAObd3tGHTYkRg3FTkpWVLdiLBwqc7M+ERU5B/GitObpFHBCgOzngFMiorF9swiuSyKIrbWleDio3q3em22dmmre1yP6oLjiI+Ok46nmpOxft4qnGmq1eYskD83x+2aP2Wp+cf8UJ51d6CwZgcc4p8zvi59FUuJIJbX/4rZS+X9AfsAjjWe9dim+e0TXH9+Wy4nTZ6O+JhJwZYm+yUwInJshHQdu2jseICe771etbW8anYrmxgkgPk9YHx4NK62NcBsNMFsnIKm1y1et7WLdrfyl5/foLkE2Hrfo6i22K+2aQkp8n7/4ACsn23QzVJ41pQZWJ6cKZevPm2QkqCLBCRMMKEi/xDCxoRJZef8X3avimlMgkpw3jAvFZZL9wwX+26eRGvXi9D5PmAkMqbOwbm8gzBGxLitGcrusj37qkjAgulpqFx7WF4COzlxpxJ7b5zgEt8ABZkWa8bZvAOyeedSufT6cZTfr+amwQAFOZRT7LZU3nllv/SQxBPi/U3O0LneOfxdOB94eJp3+SUoxJKkhfL+oH0QR26dVkQHKbngcdFqe4GPfWxefKg2ARMjJ8j7LJe6PiXAyvE+MPb3as9J74+v4MlQnwYoRPapQqgB+vsA79mAN3/7I+gcg1KBrSUWt/K00kXSG2Le0HAHQ/UyGM4X+VJZy4zkh6BzBE/vwkPhW4HRRjMF0lgLeNJPwehErXijm4LZmZrwVi+x6FRpfNFJLDtXAl/1EY8gvPBHF/EMxhJ/9QjBmOSVXCsEeiJIDSKUjCv8/28Q7NDtn6Mjobt/h6EBfgFsW3X6W7dh8QAAAABJRU5ErkJggg==',
            'important': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAB9klEQVR4nO2bPU7DQBCFZ5/SQgEn4AxIXCESouAONByANhUH4AK09LkBElegRnRQUFAkwQ5SvMhIieIlie14d2bXwyelWMvZeW92dpwf21jSDUg5A85gt5evjQtuND4xxICxkRiWSoixkRsPnQhjEzAdMhlI1byvuMYmaNxnNaAP5rvoAWew0OyjCxxBOGmrDyEnl6KNToSYNAaa6oXPyWKjiW74mCRm6vSjy5tTYZcPkHLQ99Wv84M2J6fOJl8g5YCUY6xQ+Q+vjujs4nA1fn/5pvubN/ZvjiDlQEPzc1n3CVIOSDkg5UBq/xdFdWwL3vaz9AsSYj6rZiD/cjLCBESiElHmJmCqLAH5ZFEdOwnpfwVMlVdA5hh2t0T/EzBRXgG52wTVVcB0QWQVV4AtiOZZobcHuH0gLytCMgEjpntytl0JuHvA0i9IkNWqW4VNcL0Cyl5Q9gS1CciFVv9PArj7wLIJSu1/9hslXR4fPn9fksA9IHE14MT1B1LOQCrw6fCAzq+PV+PnpxmN7z7YdWDTwb5ug02+0ObklNnmB6QcU/djdB/+LttVzejy5hSo0w8fk8RKE93wOVlMNNWLEJNK00YnQk4uQVt94AjCxT66wBksJPvqMT4u8pKfFbouBGIQIRnX/D83SOFQ++ToNtQ9O0wJ8AMPBBOC4a+drgAAAABJRU5ErkJggg==',
            'warning': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAB5UlEQVR4nOWavUrEUBCFTw6+jGBpI4iFD2EhtqKdb2FtJxKws/YR7AXfwMpa1j921wT0iuCGNexmN/fOvZNkvm6KzNyZczJJIJmDbQjjUPsA+Qmc6QFowy6or+kCwjjUKlxXXcsFhHGoUXSZ2houIIzD1AVXqZzaBYRxmLLYuuqmdAFhHKYq1FbVVC4gjMMURXzVTOECwjiMXSBUxdguIIzDmMml1Ivpgg0osXNwga39syp+fnrA7fn2cByQC6sWywWEcRgjaSy1YuQljEPphLGf29L5CSXc91djnApqqVNO3xpjqTqddUAxeWmMU0GpRG1VKcajf3E5eY1ar4MOGA3HAbmHGnUH+AxAwgWEEhIDkIChCXxVqDfcdgeE1u/GU8C5fjsgD5j+74tP+flexWXAAELOQSgyvwd654BcYAPPPwp9d0DoeQhFivGf6s6hmIYNwBf6XCT1FjZzQFl8iHwM+ZyL6MAOCFmAobDtBZJfYrMBFIH3f8j5MtezHxvX4fgKWRQH5D1ovu05CeNkTkn9zb1T7B5eVvHj/Q3uro+S3wqEcTike9/n3IRxMjdQ9dfdBYRxOHT1V/VBGIdDV39VP4RxaEH9pr4I49CK+sv6I4xDS+ov6pMwDq2pX+83M9X1An4Ac2jyq41peRAAAAAASUVORK5CYII=',
            'caution': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAEWklEQVR4nO2bbWxTVRjH//e0pS1sc2uZri9MwSEwDcaoIRo1+kElQILBiBo/YCJ+ERP3kq0d3St7dRvbGOgnNTJ0EuJMVBSJmpioKEY/MDUKg5j0Za1sYruVWlraa+5Z7u2ObNiZjeze4y9pznme3nPuuU/OOc/z3JMriOAbAs7Ry5Xhktu5mwzrz54SuJ8BBJxDwDkEnEPAOQScQ8A5BJxDwDkEnEPAOQScQ8A5BJxDwDkEnEPAOQSco5/vDs3r1qBk6C0IBoOi81bUIPzhsTn3JRiNWP3uIZjW3jKlEEX89twuTH55YvHOgL9+OY1Q36uMztHkgcFeNOe+HPWuzMMDGHvt4Lw+/IItAWmgF7/7QZF1uTko7m4FSPa3K9i6GZbt2xQ5dupHhHoOqGQPSKfhrfIgNRlVVMvuvhPXP/9sVs1NJavgaK5VZKkf70suiJcvq2cTTI6GEGhsY3Q3lL0A822lVx+Q2Yzi/d20lPF7mpAIjKrPC4Q/+Bjho5nNT9DrUdzTBmI2zdrGscdDZ4DMhcNDiBz7VL1uMNDQhmQwpMjGlTfBVlM547WWJ7eh4LEtihw/cxajrZ0LOj6yoL1L63diEr6qWrovyFiffgJ5Dz3AXCft9o46lyKn45fgLXPRUvWBUPTk9xh74xCjc7Y1QF+QPzUIsxk39ndSvy8z2vwy4iPntBMJhnoOIP7rGUXWL7fC3lBD6/baKro0ZMIfHceFI+9dk3GRa3IXKYhLJmlEKF7KTOn8zY/C5ipn/H3C50egdo82c4H4yDkEu/oZXeHOHUpd8vPeMjdS0YvaTYbGBwYx+dU3M/4X2rsfseGfNJ4NiiL81XVIRSYYdWz4Z4y9PsBHOmyw20CWLWV05tI1MN+6TvsG0EmJUV8HjQqnk02UqAkDOFrqscTpyCimBUhXixI1YQDLU48jf9Mjipzw+uCt3M1cM1OUqAkDmFbfDLunmtH561oQPvoJ/U3H2d4IvdWiHQMQkxHF+zppKTM+8A6iJ07SeqCxHcnfzyv/SQ/v7GjSjgHsnmo6A2Tip0cQ7OxT5FQkAl91HXWRMnkP3g/rM9vVb4DrNj5M1z6T5ZW7mZBYQpoN42++zehs7koYV61UrwGWOOxwttYzumD73lmzvGB3P5Mw0aXT236Fy1SFAQSdDsW9HdDl5Sq6ic+/wB+DR2ZtIyYS1CtIpYy5dC2KynepzwBFFS9i6R3rFTl5fgw+d8O/tpPeAgW79l2RMOVsuEs9Bsi5dwMKp78BTqfpW6FUOJJV+/GDg4h+/W1GQQhWdLUws2nRGkBvtUydAQgCc04gu7ysEEXqFSTvIGOwFdEDlsVtAEHAiu5W6AuXM1leqPeVOXclLRm/p5nR5W/ZSA9MFq0BCnfuQO599yhyOhaDt8L9nw80Isc/w59D7zM6e+Nu6l3mC0EOPf7/XoBTCDiHgHMIOIeAcwg4h4BzCDiHgHMIOIeAcwg4R+Dui+l/8DdPUmCshb5/FAAAAABJRU5ErkJggg==',
            'markdown-alert-note': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABgElEQVR4nO2bu03EQBRF7xxthEROBVSwrdAAGX3QAzExrRATkJHQANIGJEZCAlkr7/o3X989kgNb9nv3jt/Y45EndPIGmbPLmezq4X1ywR2eboMyELpKDJdqkNBVbjx1Q4SuAdMpG4NWzcfKG7oGjcesBrZgfo0eciZLzRJd5EiSk7n6SBm8FHN0kiJoDUzVS8xgtTFFNzGC1MyYftZc3ArnfCBz2PrdH/PDnJNbZ8gXMgeZE7pC5X+3v9bz/c3//v7xQ2+f39m/HJE5ODz8jun7RObsSiV+ef363UqDzMGt/x/7RebsSiUuOQ7og8xB5iBzkDnIHGQOMgeZQ+5/cmrhzy8yB5mDzKG/4/IcuEyKnusCh41XwbE/ZA4yh6GDW+0GQ76Yc3LLnPKDzAljc+FbmC4/V82subgFxvQTI0itTNFNzGA1MVUvKYKWZo5OUgYvwVx95EiSiyW6yJksJUv1hBgv+ZJjhbU3ghpElMwbLusGlQ7blaOnsFs7rAb4AedJsUM6zwafAAAAAElFTkSuQmCC',
            'markdown-alert-tip': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAADsklEQVR4nO2ba0gUURiG3/lay2ubWbawUmFIYUJiZlT0x/JPRkIXQcMKC4SCflUE/siECroXlGB0U0FByiCKjEKy2xqBUmYXMbJaXIvKrKzU3Ykd2sktda/nzMxODwzMGc453/t+c2bOmWFGEKFvCDrHwDOYedd8rwecdXeTAA4IokoMK5UQQVS5cdaJEEQNmGaZDNKq+WDFFUQNGg/maKBQMB+IHuIZjDX+6CIeQXjiqz5i2blS+KKTWHSqBrzVS8HsTG14o5uC0Yma8aSfAmmsFUbzQdA5FOpn35Mf8qWy1hnOF0HnEHSOIHIc/jHjopCbmo3FiRmYbUpCbKQRJBA+9X1Gx4dOWDpbUNtyBW96usDryVHglYCC9JUoztoiJWE07A4Hapovo6T+KPr6v/NNgJmR+T3LtmFDxmqf2jx/9xJrzm/Gh289TJNgAGM2zs/9x/yFR9dQ9bAObd3tGHTYkRg3FTkpWVLdiLBwqc7M+ERU5B/GitObpFHBCgOzngFMiorF9swiuSyKIrbWleDio3q3em22dmmre1yP6oLjiI+Ok46nmpOxft4qnGmq1eYskD83x+2aP2Wp+cf8UJ51d6CwZgcc4p8zvi59FUuJIJbX/4rZS+X9AfsAjjWe9dim+e0TXH9+Wy4nTZ6O+JhJwZYm+yUwInJshHQdu2jseICe771etbW8anYrmxgkgPk9YHx4NK62NcBsNMFsnIKm1y1et7WLdrfyl5/foLkE2Hrfo6i22K+2aQkp8n7/4ACsn23QzVJ41pQZWJ6cKZevPm2QkqCLBCRMMKEi/xDCxoRJZef8X3avimlMgkpw3jAvFZZL9wwX+26eRGvXi9D5PmAkMqbOwbm8gzBGxLitGcrusj37qkjAgulpqFx7WF4COzlxpxJ7b5zgEt8ABZkWa8bZvAOyeedSufT6cZTfr+amwQAFOZRT7LZU3nllv/SQxBPi/U3O0LneOfxdOB94eJp3+SUoxJKkhfL+oH0QR26dVkQHKbngcdFqe4GPfWxefKg2ARMjJ8j7LJe6PiXAyvE+MPb3as9J74+v4MlQnwYoRPapQqgB+vsA79mAN3/7I+gcg1KBrSUWt/K00kXSG2Le0HAHQ/UyGM4X+VJZy4zkh6BzBE/vwkPhW4HRRjMF0lgLeNJPwehErXijm4LZmZrwVi+x6FRpfNFJLDtXAl/1EY8gvPBHF/EMxhJ/9QjBmOSVXCsEeiJIDSKUjCv8/28Q7NDtn6Mjobt/h6EBfgFsW3X6W7dh8QAAAABJRU5ErkJggg==',
            'markdown-alert-important': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAB9klEQVR4nO2bPU7DQBCFZ5/SQgEn4AxIXCESouAONByANhUH4AK09LkBElegRnRQUFAkwQ5SvMhIieIlie14d2bXwyelWMvZeW92dpwf21jSDUg5A85gt5evjQtuND4xxICxkRiWSoixkRsPnQhjEzAdMhlI1byvuMYmaNxnNaAP5rvoAWew0OyjCxxBOGmrDyEnl6KNToSYNAaa6oXPyWKjiW74mCRm6vSjy5tTYZcPkHLQ99Wv84M2J6fOJl8g5YCUY6xQ+Q+vjujs4nA1fn/5pvubN/ZvjiDlQEPzc1n3CVIOSDkg5UBq/xdFdWwL3vaz9AsSYj6rZiD/cjLCBESiElHmJmCqLAH5ZFEdOwnpfwVMlVdA5hh2t0T/EzBRXgG52wTVVcB0QWQVV4AtiOZZobcHuH0gLytCMgEjpntytl0JuHvA0i9IkNWqW4VNcL0Cyl5Q9gS1CciFVv9PArj7wLIJSu1/9hslXR4fPn9fksA9IHE14MT1B1LOQCrw6fCAzq+PV+PnpxmN7z7YdWDTwb5ug02+0ObklNnmB6QcU/djdB/+LttVzejy5hSo0w8fk8RKE93wOVlMNNWLEJNK00YnQk4uQVt94AjCxT66wBksJPvqMT4u8pKfFbouBGIQIRnX/D83SOFQ++ToNtQ9O0wJ8AMPBBOC4a+drgAAAABJRU5ErkJggg==',
            'markdown-alert-warning': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAB5UlEQVR4nOWavUrEUBCFTw6+jGBpI4iFD2EhtqKdb2FtJxKws/YR7AXfwMpa1j921wT0iuCGNexmN/fOvZNkvm6KzNyZczJJIJmDbQjjUPsA+Qmc6QFowy6or+kCwjjUKlxXXcsFhHGoUXSZ2houIIzD1AVXqZzaBYRxmLLYuuqmdAFhHKYq1FbVVC4gjMMURXzVTOECwjiMXSBUxdguIIzDmMml1Ivpgg0osXNwga39syp+fnrA7fn2cByQC6sWywWEcRgjaSy1YuQljEPphLGf29L5CSXc91djnApqqVNO3xpjqTqddUAxeWmMU0GpRG1VKcajf3E5eY1ar4MOGA3HAbmHGnUH+AxAwgWEEhIDkIChCXxVqDfcdgeE1u/GU8C5fjsgD5j+74tP+flexWXAAELOQSgyvwd654BcYAPPPwp9d0DoeQhFivGf6s6hmIYNwBf6XCT1FjZzQFl8iHwM+ZyL6MAOCFmAobDtBZJfYrMBFIH3f8j5MtezHxvX4fgKWRQH5D1ovu05CeNkTkn9zb1T7B5eVvHj/Q3uro+S3wqEcTike9/n3IRxMjdQ9dfdBYRxOHT1V/VBGIdDV39VP4RxaEH9pr4I49CK+sv6I4xDS+ov6pMwDq2pX+83M9X1An4Ac2jyq41peRAAAAAASUVORK5CYII=',
            'markdown-alert-caution': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAEWklEQVR4nO2bbWxTVRjH//e0pS1sc2uZri9MwSEwDcaoIRo1+kElQILBiBo/YCJ+ERP3kq0d3St7dRvbGOgnNTJ0EuJMVBSJmpioKEY/MDUKg5j0Za1sYruVWlraa+5Z7u2ObNiZjeze4y9pznme3nPuuU/OOc/z3JMriOAbAs7Ry5Xhktu5mwzrz54SuJ8BBJxDwDkEnEPAOQScQ8A5BJxDwDkEnEPAOQScQ8A5BJxDwDkEnEPAOQSco5/vDs3r1qBk6C0IBoOi81bUIPzhsTn3JRiNWP3uIZjW3jKlEEX89twuTH55YvHOgL9+OY1Q36uMztHkgcFeNOe+HPWuzMMDGHvt4Lw+/IItAWmgF7/7QZF1uTko7m4FSPa3K9i6GZbt2xQ5dupHhHoOqGQPSKfhrfIgNRlVVMvuvhPXP/9sVs1NJavgaK5VZKkf70suiJcvq2cTTI6GEGhsY3Q3lL0A822lVx+Q2Yzi/d20lPF7mpAIjKrPC4Q/+Bjho5nNT9DrUdzTBmI2zdrGscdDZ4DMhcNDiBz7VL1uMNDQhmQwpMjGlTfBVlM547WWJ7eh4LEtihw/cxajrZ0LOj6yoL1L63diEr6qWrovyFiffgJ5Dz3AXCft9o46lyKn45fgLXPRUvWBUPTk9xh74xCjc7Y1QF+QPzUIsxk39ndSvy8z2vwy4iPntBMJhnoOIP7rGUXWL7fC3lBD6/baKro0ZMIfHceFI+9dk3GRa3IXKYhLJmlEKF7KTOn8zY/C5ipn/H3C50egdo82c4H4yDkEu/oZXeHOHUpd8vPeMjdS0YvaTYbGBwYx+dU3M/4X2rsfseGfNJ4NiiL81XVIRSYYdWz4Z4y9PsBHOmyw20CWLWV05tI1MN+6TvsG0EmJUV8HjQqnk02UqAkDOFrqscTpyCimBUhXixI1YQDLU48jf9Mjipzw+uCt3M1cM1OUqAkDmFbfDLunmtH561oQPvoJ/U3H2d4IvdWiHQMQkxHF+zppKTM+8A6iJ07SeqCxHcnfzyv/SQ/v7GjSjgHsnmo6A2Tip0cQ7OxT5FQkAl91HXWRMnkP3g/rM9vVb4DrNj5M1z6T5ZW7mZBYQpoN42++zehs7koYV61UrwGWOOxwttYzumD73lmzvGB3P5Mw0aXT236Fy1SFAQSdDsW9HdDl5Sq6ic+/wB+DR2ZtIyYS1CtIpYy5dC2KynepzwBFFS9i6R3rFTl5fgw+d8O/tpPeAgW79l2RMOVsuEs9Bsi5dwMKp78BTqfpW6FUOJJV+/GDg4h+/W1GQQhWdLUws2nRGkBvtUydAQgCc04gu7ysEEXqFSTvIGOwFdEDlsVtAEHAiu5W6AuXM1leqPeVOXclLRm/p5nR5W/ZSA9MFq0BCnfuQO599yhyOhaDt8L9nw80Isc/w59D7zM6e+Nu6l3mC0EOPf7/XoBTCDiHgHMIOIeAcwg4h4BzCDiHgHMIOIeAcwg4R+Dui+l/8DdPUmCshb5/FAAAAABJRU5ErkJggg==',
        }
        
        # Find both standard admontions and any potential markdown-alerts
        alerts = soup.find_all(class_=lambda x: x and ('markdown-alert' in x or 'admonition' in x))
        print(f"DEBUG: Found {len(alerts)} alerts/admonitions to transform.")
        
        for alert in alerts:
            try:
                classes = alert.get('class', [])
                
                # Determine type. Usually ['admonition', 'note'] or ['markdown-alert', 'markdown-alert-note']
                # Filter for known types
                known_types = ['note', 'tip', 'critical', 'important', 'warning', 'caution', 
                               'markdown-alert-note', 'markdown-alert-tip', 'markdown-alert-important', 'markdown-alert-warning', 'markdown-alert-caution']
                
                alert_type_cls = next((c for c in classes if c in known_types), 'note')
                
                # Verify it IS an alert we want to style (skip if it's just 'admonition' with no typed class, though unlikely)
                if alert_type_cls == 'admonition': 
                     # fallback if only 'admonition' present, default to note?
                     alert_type_cls = 'note'

                icon = alert_icons.get(alert_type_cls, 'ℹ️')
                
                # Create 1x1 Table with aggressive resets
                table = factory_soup.new_tag('table')
                # Map standardized class for CSS: always use markdown-alert-TYPE style logic or keep admonition?
                # The existing CSS uses .alert-table.markdown-alert-note etc.
                # We should normalize the class name on the table to match CSS expectations.
                
                # Normalize type for CSS
                css_type_map = {
                    'note': 'markdown-alert-note',
                    'tip': 'markdown-alert-tip',
                    'important': 'markdown-alert-important',
                    'warning': 'markdown-alert-warning',
                    'caution': 'markdown-alert-caution',
                    'critical': 'markdown-alert-caution' # map critical to caution
                }
                final_css_class = css_type_map.get(alert_type_cls, alert_type_cls)
                if not final_css_class.startswith('markdown-alert-'):
                     final_css_class = 'markdown-alert-note' # Fallback
                
                table['class'] = f"alert-table {final_css_class}"
                table['style'] = "width: 100%; border-collapse: collapse; margin-bottom: 16px;"
                table['cellpadding'] = "0"
                table['cellspacing'] = "0"
                table['border'] = "0"
                
                tr = factory_soup.new_tag('tr')
                td = factory_soup.new_tag('td')
                td['class'] = "alert-cell"
                td['valign'] = "top"
                
                # Construct Content: Title + Flat Body
                
                # 1. Title Line
                # Admonition title class is .admonition-title
                # GitHub alert title class is .markdown-alert-title
                title_node = alert.find(class_=['markdown-alert-title', 'admonition-title'])
                title_text = title_node.get_text() if title_node else alert_type_cls.title()
                
                # Create clean bold title with icon
                # <b><img src="data..." style="..."/> Title</b><br>
                b_tag = factory_soup.new_tag('b')
                
                # Use Image for Icon (High Fidelity, Robust Color)
                icon_img = factory_soup.new_tag('img')
                icon_img['src'] = icon
                # Sizing: 1em approx (16px) or slightly larger. Vertical align middle.
                icon_img['style'] = "width: 16px; height: 16px; vertical-align: middle; margin-right: 5px;"
                
                b_tag.append(icon_img)
                b_tag.append(f" {title_text}")
                
                td.append(b_tag)
                td.append(factory_soup.new_tag('br'))
                
                # 2. Body Content (Flattened)
                # Skip the separate title node if it was in children
                for child in list(alert.contents):
                    if child == title_node: continue
                    if child.name == 'p':
                        # Append paragraph contents inline
                        for p_child in list(child.contents):
                            td.append(p_child)
                        # Add breaks to simulate paragraph spacing
                        td.append(factory_soup.new_tag('br'))
                        td.append(factory_soup.new_tag('br'))
                    elif child.name == 'div':
                        # Recurse or just append? Flattening complex divs is hard.
                        # For simple alerts, we just append.
                        td.append(child)
                    else:
                        # Text nodes, etc.
                        td.append(child)
                
                tr.append(td)
                table.append(tr)
                alert.replace_with(table)
            except Exception as inner_e:
                print(f"DEBUG: Error transforming specific alert: {inner_e}")
                import traceback
                traceback.print_exc()
                continue

        # 5. Wrap Emojis in <img> tags (Runtime Generation)
        # xhtml2pdf fails to render Color Emojis from fonts correctly (clipping/sizing).
        # We use PIL to generate a high-fidelity PNG of the emoji using the system font
        # and inject it as a Base64 image.
        
        from PIL import Image, ImageDraw, ImageFont
        import base64
        import io
        from functools import lru_cache
        
        @lru_cache(maxsize=128)
        def get_emoji_base64(char):
            try:
                # Target Windows Emoji font first (most likely env)
                # If on Linux/Mac, this path won't exist, need fallback
                font_paths = [
                    "C:/Windows/Fonts/seguiemj.ttf", # Windows Color Emoji
                    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", # Linux
                    "/System/Library/Fonts/Apple Color Emoji.ttc", # Mac
                    "arial.ttf" # Fallback
                ]
                
                font_path = "arial.ttf"
                for p in font_paths:
                    if os.path.exists(p):
                        font_path = p
                        break
                
                # Render large for quality
                size = 64
                font = ImageFont.truetype(font_path, size)
                
                # Create Image (Transparent)
                # Add padding to ensure no clipping during render
                # Emojis are often square-ish.
                img = Image.new('RGBA', (int(size*1.5), int(size*1.5)), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Check for Color support (PIL 10+)
                # embedded_color=True works for fonts with CBDT/CBLC (Google) or SBIX (Apple).
                # COLR (Windows) support is partial in basic PIL, requires libraqm for complex layout,
                # but often renders basic shapes. Even B&W is better than broken PDF glyphs.
                try:
                    draw.text((size//4, size//4), char, font=font, fill="black", embedded_color=True)
                except:
                    draw.text((size//4, size//4), char, font=font, fill="black")

                # Trim empty space to get tight bounding box of the glyph
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                
                # Match Alert Icon Strategy: Use larger 64x64 source
                final_img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
                
                # Resizing logic (Standard Centered)
                # Table Wrapper strategy solves clipping, so we use natural centered layout.
                # 50x50 glyph on 64x64 canvas (slight padding).
                img.thumbnail((50, 50), Image.Resampling.LANCZOS)
                
                # Center X, Center Y
                x = (64 - img.width) // 2
                y = (64 - img.height) // 2
                final_img.paste(img, (x, y))
                
                # Save to Base64 (PNG RGBA - Matching Alert Icons)
                # We previously switched to JPEG, but Alerts use PNG.
                buffer = io.BytesIO()
                final_img.save(buffer, format='PNG')
                b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8').replace('\n', '')
                
                # Log success
                print(f"DEBUG: Generated Emoji {char} as 64x64 PNG (AlertMatch).")
                return "data:image/png;base64," + b64_str
            except Exception as e:
                print(f"DEBUG: Failed to render emoji {char}: {e}")
                import traceback
                traceback.print_exc()
                return None

                return None

        # -------------------------------------------------------------------------
        # 5.5 Checklist / Task List Handling
        # -------------------------------------------------------------------------
        # Moved here to utilize 'get_emoji_base64' for consistent high-quality icons.
        
        task_items = soup.find_all('li', class_='task-list-item')
        if task_items:
            print(f"DEBUG: Found {len(task_items)} task list items to transform.")
            
        for li in task_items:
            checkbox = li.find('input', type='checkbox')
            if not checkbox: continue
            
            is_checked = checkbox.has_attr('checked')
            
            # visual chars: ☑ (2611) / ☐ (2610)
            # We treat them as emojis to generate the image
            char = '\u2611' if is_checked else '\u2610'
            b64_icon = get_emoji_base64(char)
            
            if b64_icon:
                img_tag = factory_soup.new_tag('img')
                img_tag['src'] = b64_icon
                img_tag['alt'] = "[x]" if is_checked else "[ ]"
                # Style for alignment
                img_tag['style'] = "width: 14px; height: 14px; vertical-align: middle; margin-right: 6px;"
                
                # Replace input with image
                checkbox.replace_with(img_tag)
                
                # Remove 'task-list-item' class or style it to remove default bullet?
                # Usually standard CSS handles 'list-style: none' for task-list-item.
                # We enforce it to be sure.
                if 'style' in li.attrs:
                    li['style'] += "; list-style-type: none;"
                else:
                    li['style'] = "list-style-type: none;"
            else:
                 # Fallback if image gen fails
                 new_span = factory_soup.new_tag('span')
                 new_span.string = "[x] " if is_checked else "[ ] "
                 new_span['style'] = "font-family: monospace; font-weight: bold; margin-right: 5px;"
                 checkbox.replace_with(new_span)
                 li['style'] = "list-style-type: none;"


        # Regex for common emoji ranges
        emoji_pattern = re.compile(
            r'[\U00010000-\U0010ffff]'  # SMP (contains most emojis)
            r'|[\u2600-\u27ff]'         # Misc Symbols
            r'|[\u2300-\u23ff]'         # Misc Technical
            r'|[\u2b50]'                # Star
            r'|[\u203c-\u2049]'         # Punctuation
        )

        # Fallback Map for Shortcodes -> Unicode (since 'emoji' lib is not installed)
        # This allows us to fix images generated by pymdownx.emoji
        SHORTCODE_MAP = {
            ':rocket:': '🚀',
            ':tada:': '🎉',
            ':snake:': '🐍',
            ':heart:': '❤️',
            ':warning:': '⚠️',
            ':note:': 'ℹ️',
            ':tip:': '💡',
            ':important:': '💜',
            ':caution:': '🛑',
            ':smile:': '😄',
            ':thumbsup:': '👍',
            ':thumbsdown:': '👎',
            ':check:': '✅',
            ':x:': '❌'
        }
        
        def emoji_replacer(match):
            char = match.group(0)
            b64_src = get_emoji_base64(char)
            if b64_src:
                # Use Standard Style (Middle)
                # With Global Line Height 1.5, trimming should be gone.
                return f'<b><img src="{b64_src}" alt="emoji" style="width: 14px; height: 14px; vertical-align: middle; margin: 0 1px;" /></b>'
            return char
                
        # 1. Replace Text Emojis
        for text_node in soup.find_all(string=True):
            if text_node.parent.name in ['script', 'style', 'pre', 'code', 'span', 'div'] and 'emoji' in (text_node.parent.get('class') or []):
                 pass # Already processed or effectively wrapped
            
            text = str(text_node)
            if emoji_pattern.search(text):
                new_html = emoji_pattern.sub(emoji_replacer, text)
                if new_html != text:
                    new_nodes = BeautifulSoup(new_html, 'html.parser')
                    text_node.replace_with(new_nodes)

        # 2. Replace Existing Emoji Images (from pymdownx.emoji or generic)
        # Scan ALL images to find emoji candidates
        all_imgs = soup.find_all('img')
        print(f"DEBUG: Found {len(all_imgs)} images in document.")
        
        for img in all_imgs:
            classes = img.get('class', [])
            alt_text = img.get('alt', '')
            src_text = img.get('src', '')
            
            # log for visibility
            print(f"DEBUG: Inspecting IMG - Class: {classes}, Alt: {alt_text}, Src: {src_text[:50]}...")
            
            is_emoji = False
            # Check Class
            if classes and any(x in classes for x in ['emoji', 'emojione', 'gemoji', 'twemoji']):
                is_emoji = True
            
            # Check Src (EmojiOne/Twemoji CDN)
            if 'emojione' in src_text or 'twemoji' in src_text or 'gemoji' in src_text:
                is_emoji = True
                
            # Check Alt (Shortcode format) and map availability
            shortcode = alt_text
            unicode_char = SHORTCODE_MAP.get(shortcode)
            
            if is_emoji or unicode_char:
                if unicode_char:
                    # Best case: we have the character
                    b64_src = get_emoji_base64(unicode_char)
                    if b64_src:
                        # --- VISIBLE ALIGNMENT: Middle ---
                        # Create wrapper (B tag helps sometimes with spacing)
                        b_wrapper = factory_soup.new_tag("b")
                        
                        img['src'] = b64_src
                        if 'width' in img.attrs: del img['width']
                        if 'height' in img.attrs: del img['height']
                        if 'class' in img.attrs: del img['class']
                        
                        img['style'] = "width: 14px; height: 14px; vertical-align: middle; margin: 0 1px;"
                        
                        # Create new img inside wrapper to ensure clean attributes
                        new_img = factory_soup.new_tag("img")
                        new_img['src'] = b64_src
                        new_img['style'] = "width: 14px; height: 14px; vertical-align: middle; margin: 0 1px;"
                        
                        b_wrapper.append(new_img)
                        img.replace_with(b_wrapper)
                        
                        print(f"DEBUG: REPLACED Emoji {shortcode} with Visible-Style (B+PNG+Middle).")
                    else:
                        print(f"DEBUG: Failed to render emoji char {unicode_char}")
                elif emoji_pattern.search(alt_text):
                     # Alt might be raw unicode?
                     b64_src = get_emoji_base64(alt_text)
                     if b64_src:
                        # --- VISIBLE ALIGNMENT: Middle ---
                        # Create wrapper
                        b_wrapper = factory_soup.new_tag("b")
                        new_img = factory_soup.new_tag("img")
                        new_img['src'] = b64_src
                        new_img['style'] = "width: 14px; height: 14px; vertical-align: middle; margin: 0 1px;"
                        b_wrapper.append(new_img)
                        img.replace_with(b_wrapper)

                        print(f"DEBUG: REPLACED Emoji (Unicode) {alt_text} with Visible-Style (B+PNG+Middle).")
            else:
                pass # Not an emoji image

        # 3. Wrap Blocks with Emojis in Tables (Fix for Clipping)
        # xhtml2pdf clips inline images in paragraphs. It does NOT clip them in tables.
        # Extensions: Handle <p> and <li>.
        
        blocks_to_wrap = set()
        
        for img in soup.find_all('img'):
            # Detect our emojis by style (width: 14px) or if we added a marker
            # Also blindly wrap ANY 'gemoji' class if we missed replacement (fallback)
            style = img.get('style', '')
            classes = img.get('class', [])
            
            should_wrap = False
            if "14px" in style and "margin" in style:
                should_wrap = True
            elif classes and any(x in classes for x in ['emoji', 'gemoji', 'emojione']):
                should_wrap = True
                
            if should_wrap:
                # Find parent block. Prioritize Headings > Paragraphs > Lists
                parent = img.find_parent(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if parent:
                    blocks_to_wrap.add(parent)
                    
        print(f"DEBUG: Wrapping {len(blocks_to_wrap)} blocks (p/li/h*) containing emojis in tables.")
        
        for block in blocks_to_wrap:
            # Create Table Structure
            table = factory_soup.new_tag("table")
            table['style'] = "width: 100%; border-collapse: collapse; margin-bottom: 0px;"
            table['border'] = "0"
            table['cellpadding'] = "0"
            
            tr = factory_soup.new_tag("tr")
            
            # --- SPECIAL HANDLING FOR LIST ITEMS (LI) ---
            # xhtml2pdf swallows standard bullets when a block (table) is inside <li>.
            # We must SIMULATE the bullet using a 2-column table.
            if block.name == 'li':
                # Force disable native bullet
                if 'style' in block.attrs:
                    block['style'] += "; list-style-type: none;"
                else:
                    block['style'] = "list-style-type: none;"
                    
                # Col 1: Bullet
                td_bullet = factory_soup.new_tag("td")
                td_bullet['valign'] = "top"
                td_bullet['align'] = "right"
                td_bullet['width'] = "10" # Tighter width
                # Standard bullet char.
                td_bullet.string = "•" 
                # Adjust padding and size to align better with text baseline
                td_bullet['style'] = "padding-right: 4px; font-size: 1em; line-height: 1.2; border: none;"
                tr.append(td_bullet)
                
            # Col 2 (or 1): Content
            td = factory_soup.new_tag("td")
            
            # COPY ATTRIBUTES from Block to TD
            if 'class' in block.attrs:
                td['class'] = block['class']
            
            # Merge styles
            base_style = "border: none; padding: 0; vertical-align: top; color: black; font-family: Helvetica, Arial, sans-serif;"
            block_style = block.get('style', '')
            td['style'] = f"{base_style} {block_style}"
            
            # Move contents
            # We must list(contents) because moving modifies the list
            contents = list(block.contents)
            for item in contents:
                td.append(item)
            
            tr.append(td)
            table.append(tr)
            
            # For H1-H6 and LI, we put the table INSIDE the block to preserve TOC and List structure.
            # for P, we REPLACE the block because P cannot contain Table.
            if block.name == 'p':
                block.replace_with(table)
            else:
                # h1-h6, li
                block.append(table)
        
        # Update CSS for .emoji-img - RETURNING IT instead of appending

        # 6. Transform Math (KaTeX/MathJax) -> Clean TeX
        # Note: We prioritize extracting from 'annotation' tags which contain clean LaTeX.
        for katex_node in soup.find_all(class_='katex'):
             # This loop handles KaTeX HTML structure if present, trying to replace it with a cleaner '$$...$$' block
             # However, our main logic below (CodeCogs) will handle the conversion to Image.
             # This block is for text-fallback or if we skip image generation.
             # For now, we leave this as-is or we can remove it if it conflicts. 
             # Actually, the user's "last commit" might have removed this? 
             # Let's align with the .bak file which kept it but added the CodeCogs logic after.
             pass

        # -------------------------------------------------------------------------
        # Math Transformation: Latex Script/Span -> Image (CodeCogs API)
        # -------------------------------------------------------------------------
        
        # Arithmatex output can be <script type="math/tex"> (Legacy/MathJax) OR <span class="arithmatex">\(..\)</span> (Generic)
        
        # 1. Collect potential math nodes
        candidates = []
        candidates.extend(soup.find_all('script', type=re.compile(r'math/tex')))
        candidates.extend(soup.find_all(class_='arithmatex'))
        
        if candidates:
            print(f"DEBUG: Found {len(candidates)} Math formula candidates.")
            
        processed_ids = set()
        
        for node in candidates:
            if id(node) in processed_ids:
                continue
                
            target_node = node
            parent = node.parent
            if node.name == 'script' and parent and ('arithmatex' in (parent.get('class') or []) or 'MathJax' in str(parent.get('class') or [])):
                target_node = parent
            
            if id(target_node) in processed_ids:
                continue
            
            # Extract TeX
            tex = ""
            is_display = False
            
            try:
                # STRATEGY:
                # 1. Script <script type="math/tex"> (Legacy MathJax) - Most reliable if present.
                # 2. Annotation <annotation encoding="application/x-tex"> (Modern KaTeX/MathJax) - Cleanest source for HTML output.
                # 3. Regex on raw HTML (Fallback) - Catches \(..\) if structure is weird.
                # 4. get_text() (Last Resort) - Often dirty with preview text.
                
                script_child = target_node if target_node.name == 'script' else target_node.find('script', type=re.compile(r'math/tex'))
                annotation_child = target_node.find('annotation', attrs={'encoding': 'application/x-tex'})
                
                if script_child:
                    tex = script_child.get_text()
                    is_display = 'mode=display' in script_child.get('type', '')
                    processed_ids.add(id(script_child))
                    
                elif annotation_child:
                    tex = annotation_child.get_text().strip()
                    is_display = (target_node.name == 'div') or ('display' in target_node.get('class', [])) or ('katex-display' in target_node.decode_contents())
                
                else:
                    # Fallback Regex
                    node_html = str(target_node)
                    inline_match = re.search(r'\\\((.*?)\\\)', node_html, re.DOTALL)
                    block_match = re.search(r'\\\[(.*?)\\\]', node_html, re.DOTALL)
                    
                    if inline_match:
                        tex = inline_match.group(1).strip()
                        is_display = False
                    elif block_match:
                        tex = block_match.group(1).strip()
                        is_display = True
                    else:
                        raw_text = target_node.get_text().strip()
                        if raw_text.startswith('\\(') and raw_text.endswith('\\)'):
                            tex = raw_text[2:-2]
                            is_display = False
                        elif raw_text.startswith('\\[') and raw_text.endswith('\\]'):
                            tex = raw_text[2:-2]
                            is_display = True
                        else:
                            tex = raw_text
                            is_display = (target_node.name == 'div')
                            
                if not tex or not tex.strip():
                    continue

                # Encode TeX for URL (CodeCogs)
                base_url = "https://latex.codecogs.com/png.image"
                params = f"\\dpi{{300}} {tex}"
                safe_params = urllib.parse.quote(params)
                url = f"{base_url}?{safe_params}"
                
                # Fetch image with User-Agent
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    img_b64 = base64.b64encode(response.content).decode('ascii')
                    data_uri = f"data:image/png;base64,{img_b64}"
                    
                    img_tag = factory_soup.new_tag('img')
                    img_tag['src'] = data_uri
                    
                    if is_display:
                        # Block Math
                        # Check context: Inside List?
                        is_inside_list = target_node.find_parent('li') is not None
                        
                        if is_inside_list:
                            # Left Align in Lists to preserve bullet flow
                            table = factory_soup.new_tag('table', attrs={'border': '0'}) # auto width
                            tr = factory_soup.new_tag('tr')
                            td = factory_soup.new_tag('td', attrs={'align': 'left', 'valign': 'middle'})
                            img_tag['style'] = "max-width: 90%;" # reduce max width slightly
                        else:
                            # Center Align in Main Body
                            table = factory_soup.new_tag('table', attrs={'width': '100%', 'border': '0'})
                            tr = factory_soup.new_tag('tr')
                            td = factory_soup.new_tag('td', attrs={'align': 'center', 'valign': 'middle'})
                            img_tag['style'] = "width: 60%;" 
                            
                        td.append(img_tag)
                        tr.append(td)
                        table.append(tr)
                        target_node.replace_with(table)
                        processed_ids.add(id(target_node))
                    else:
                        # INLINE MATH: Use Native Text + Sub/Sup
                        replacement = parse_tex_to_html(factory_soup, tex)
                        replacement['class'] = "math-inline-text"
                        target_node.replace_with(replacement)
                        processed_ids.add(id(target_node))
                else:
                    print(f"DEBUG: Math render failed: {response.status_code}")
                    # Fallback
                    new_span = factory_soup.new_tag('span')
                    new_span.string = f"${tex}$"
                    target_node.replace_with(new_span)
                    
            except Exception as e:
                print(f"DEBUG: Math rendering exception: {e}")
                # Fallback safely
                try:
                    new_span = factory_soup.new_tag('span')
                    new_span.string = f"${tex}$"
                    target_node.replace_with(new_span)
                except:
                    pass
        # We fetch a generic PNG render from CodeCogs to embed in PDF
        
        math_scripts = soup.find_all('script', type=re.compile(r'math/tex'))
        if math_scripts:
            print(f"DEBUG: Found {len(math_scripts)} Math formulas to render.")
            
        for script in math_scripts:
            try:
                tex = script.get_text()
                is_display = 'mode=display' in script.get('type', '')
                
                # Encode TeX for URL
                # Add decent DPI for print quality
                base_url = "https://latex.codecogs.com/png.image"
                params = f"\\dpi{{300}} {tex}"
                safe_params = urllib.parse.quote(params)
                url = f"{base_url}?{safe_params}"
                
                print(f"DEBUG: Fetching Math Render: {tex[:20]}...")
                
                # Fetch image
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    # Convert to Base64
                    img_b64 = base64.b64encode(response.content).decode('ascii')
                    data_uri = f"data:image/png;base64,{img_b64}"
                    
                    # Create Img Tag
                    img_tag = factory_soup.new_tag('img')
                    img_tag['src'] = data_uri
                    
                    # Styling
                    if is_display:
                        # Block Math
                        # Block Math
                        is_inside_list = script.find_parent('li') is not None
                        
                        if is_inside_list:
                            # Left Align in Lists
                            table = factory_soup.new_tag('table', attrs={'border': '0'})
                            tr = factory_soup.new_tag('tr')
                            td = factory_soup.new_tag('td', attrs={'align': 'left', 'valign': 'middle'})
                            img_tag['style'] = "max-width: 90%;"
                        else:
                            # Center Align in Main Body
                            table = factory_soup.new_tag('table', attrs={'width': '100%', 'border': '0'})
                            tr = factory_soup.new_tag('tr')
                            td = factory_soup.new_tag('td', attrs={'align': 'center', 'valign': 'middle'})
                            img_tag['style'] = "width: 60%;" 

                        td.append(img_tag)
                        tr.append(td)
                        table.append(tr)
                        script.replace_with(table)
                    else:
                        # INLINE MATH: Text
                        replacement = parse_tex_to_html(factory_soup, tex)
                        script.replace_with(replacement)
                else:
                    print(f"DEBUG: Math render failed: {response.status_code}")
                    # Fallback to text
                    replacement = parse_tex_to_html(factory_soup, tex)
                    script.replace_with(replacement)
                    
            except Exception as e:
                print(f"DEBUG: Math rendering exception: {e}")
                # Fallback
                try:
                    replacement = parse_tex_to_html(factory_soup, tex)
                    script.replace_with(replacement)
                except:
                    pass
            
        # -------------------------------------------------------------------------
        # -------------------------------------------------------------------------
        # Footnote Transformation: List -> Table (Fixes Numbering Visibility)
        # -------------------------------------------------------------------------
        # -------------------------------------------------------------------------
        # Footnote Transformation: List -> Table (Fixes Numbering Visibility)
        # -------------------------------------------------------------------------
        # Handle multiple footnote areas if present, including standard python-markdown class
        # We use CSS selectors for broader compatibility
        # Matches <div class="footnote">, <div class="footnotes">, <section class="...">
        all_notes = soup.select('div.footnote, div.footnotes, section.footnote, section.footnotes')
        
        for footnote_node in all_notes:
            # Find the list (ordered or unordered)
            ol = footnote_node.find('ol')
            if not ol:
                 ol = footnote_node.find('ul')
            
            if ol:
                # Create a new table to replace the list
                # Use legacy attributes to kill all default spacing and enforce left align
                table = factory_soup.new_tag('table', attrs={
                    'class': 'footnote-table',
                    'cellspacing': '0',
                    'cellpadding': '0',
                    'border': '0',
                    'align': 'left'
                })
                
                # Iterate through list items to create table rows
                li_items = ol.find_all('li', recursive=False)
                for index, li in enumerate(li_items, 1):
                    tr = factory_soup.new_tag('tr')
                    
                    # 1. Spacer Cell (Robust Indentation)
                    td_spacer = factory_soup.new_tag('td', attrs={
                        'width': '10', # Reduced indent
                        'valign': 'top',
                        'style': 'border: none !important;'
                    })
                    td_spacer.string = "" # Empty
                    
                    # 2. Number Cell (e.g. "[1]")
                    # Use legacy attributes for xhtml2pdf width control
                    td_num = factory_soup.new_tag('td', attrs={
                        'class': 'fn-num',
                        'width': '1%',
                        'valign': 'top',
                        'align': 'right'
                    })
                    td_num.string = f"[{index}]"
                    
                    # 2. Content Cell
                    td_content = factory_soup.new_tag('td', attrs={
                        'class': 'fn-content',
                        'valign': 'top',
                        'align': 'left'
                    })
                    # Move all children from li to td_content
                    # We must copy/move properly to preserve structure
                    td_content.extend(li.contents)
                    
                    tr.append(td_spacer)
                    tr.append(td_num)
                    tr.append(td_content)
                    table.append(tr)
                
                # Replace the old list with the new table
                ol.replace_with(table)

        # -------------------------------------------------------------------------
        # Footnote Back-Ref Fix (Replace '↩' with Safe Unicode Arrow)
        # -------------------------------------------------------------------------
        backrefs = soup.find_all('a', class_='footnote-backref')
        if backrefs:
            for link in backrefs:
                link.string = "^" 
                link['style'] = "font-family: monospace; font-weight: bold; color: #2563eb; text-decoration: none; margin-left: 5px; font-size: 1.2em;"

        # -------------------------------------------------------------------------
        # Footnote Numbering Fix (Add Brackets [1])
        # -------------------------------------------------------------------------
        refs = soup.find_all('a', class_='footnote-ref')
        if refs:
            for link in refs:
                if link.string and link.string.isdigit():
                    link.string = f"[{link.string}]"
                    link['style'] = "color: #2563eb; text-decoration: none; font-size: 80%; vertical-align: super;"

        # Remove Preview/Dummy spans
        for junk in soup.find_all(class_=['MathJax_Preview', 'katex-html']):
            if junk: junk.decompose()

        # -------------------------------------------------------------------------
        # Layout Fix: Wrap INLINE MATH in Tables
        # -------------------------------------------------------------------------
        # Similar to Emojis, we wrap inline math to prevent clipping in xhtml2pdf.
        # This is kept SEPARATE from emoji handling for clarity.
        math_blocks_to_wrap = set()
        
        # We look specifically for the class we added earlier: 'math-inline'
        for img in soup.find_all('img', class_='math-inline'):
            # Find parent block
            parent = img.find_parent(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if parent:
                math_blocks_to_wrap.add(parent)
                
        if math_blocks_to_wrap:
            print(f"DEBUG: Wrapping {len(math_blocks_to_wrap)} blocks containing inline math.")
            
        for block in math_blocks_to_wrap:
            # Create Table Structure
            table = factory_soup.new_tag("table")
            table['style'] = "width: 100%; border-collapse: collapse; margin-bottom: 0px;"
            table['border'] = "0"
            table['cellpadding'] = "0"
            
            tr = factory_soup.new_tag("tr")
            
            # --- SPECIAL HANDLING FOR LIST ITEMS (LI) ---
            # Simulate bullet if wrapping inside an LI
            if block.name == 'li':
                # Force disable native bullet
                if 'style' in block.attrs:
                    block['style'] += "; list-style-type: none;"
                else:
                    block['style'] = "list-style-type: none;"
                    
                # Col 1: Bullet
                td_bullet = factory_soup.new_tag("td")
                td_bullet['valign'] = "top"
                td_bullet['align'] = "right"
                td_bullet['width'] = "10" # Matches Emoji logic
                td_bullet.string = "•" 
                td_bullet['style'] = "padding-right: 4px; font-size: 1em; line-height: 1.2; border: none;"
                tr.append(td_bullet)
            
            # Col 2: Content
            td = factory_soup.new_tag("td")
            
            # COPY ATTRIBUTES
            if 'class' in block.attrs:
                td['class'] = block['class']
            
            # Merge styles
            base_style = "border: none; padding: 0; vertical-align: top; color: black; font-family: Helvetica, Arial, sans-serif;"
            block_style = block.get('style', '')
            td['style'] = f"{base_style} {block_style}"
            
            # Move contents
            contents = list(block.contents)
            for item in contents:
                td.append(item)
            
            tr.append(td)
            table.append(tr)
            
            if block.name == 'p':
                block.replace_with(table)
            else:
                block.append(table)

    except Exception as e:
        logger.error(f"PDFExport: transformation error: {e}")
        logger.error(traceback.format_exc())
        # We allow it to continue so we get result (even if imperfect)

# -------------------------------------------------------------------------
# Main Export Function
# -------------------------------------------------------------------------
def export_pdf(content_html: str) -> bytes:
    """
    Export content to PDF using xhtml2pdf.
    Returns bytes.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from xhtml2pdf import pisa
        # BeautifulSoup imported globally now
        
        # Regex to find CSS variable usage
        css_var_pattern = re.compile(r'var\s*\([^)]+\)')
        
        def sanitize_css(text):
            replacements = {
                'var(--color-fg-default)': '#000000',
                'var(--color-canvas-default)': '#ffffff',
                'var(--color-border-default)': '#cccccc',
                'var(--color-accent-fg)': '#0969da',
                'var(--color-neutral-muted)': '#afb8c1',
            }
            for k, v in replacements.items():
                text = text.replace(k, v)
            return css_var_pattern.sub('#888888', text)

        # 0. Clean & Restructure HTML using BeautifulSoup
        try:
            soup = BeautifulSoup(content_html, 'html.parser')

            # Identify Content Container - Try Multiple Selectors
            main_container = soup.find(id='documentContent')
            if not main_container:
                main_container = soup.find(class_='markdown-content')
            if not main_container:
                # Fallback: Try identifying by content-area (Word export style)
                main_container = soup.find(class_='content-area')

            if main_container:
                # Apply Transformations
                transform_html_for_pdf(main_container)

                # Create a fresh clean DOM with HEAD
                new_soup = BeautifulSoup('<html><head><meta charset="utf-8"></head><body></body></html>', 'html.parser')
                body = new_soup.body
                head = new_soup.head

                # Inject Emoji CSS (Critical for Visibility)
                style_tag = new_soup.new_tag('style')
                style_tag.string = """
                    .emoji-img {
                        width: 12px;
                        height: 12px;
                        vertical-align: bottom;
                        margin: 0 1px;
                        display: inline-block; /* Ensure it takes up space */
                    }
                """
                head.append(style_tag)
                
                # Append the main container
                body.append(main_container)

                # Check for MERMAID Diagrams (Server-Side Render via Mermaid.ink)
                # Since xhtml2pdf handles images well but JS not at all.
                try:
                    import requests
                    import base64
                    
                    mermaids = body.find_all(class_='mermaid')
                    if mermaids:
                         print(f"DEBUG: Found {len(mermaids)} Mermaid diagrams to render.")
                         
                    for m_div in mermaids:
                        try:
                            code = m_div.get_text().strip()
                            if not code: continue
                            
                            # Mermaid.ink expects specific encoding
                            # https://mermaid.ink/img/<base64>
                            # We use base64 of the code
                            
                            # Prepare config if needed (not supported by simple ink endpoint easily)
                            # Code structure: "graph TD..."
                            
                            graph_bytes = code.encode('utf-8')
                            base64_bytes = base64.urlsafe_b64encode(graph_bytes)
                            base64_str = base64_bytes.decode('ascii')
                            
                            url = f"https://mermaid.ink/img/{base64_str}?bgColor=F8F8F8"
                            
                            print(f"DEBUG: Fetching Mermaid Render: {url[:50]}...")
                            # Fetch with timeout
                            response = requests.get(url, timeout=5)
                            
                            if response.status_code == 200:
                                # Convert to Base64 Data URI
                                img_b64 = base64.b64encode(response.content).decode('ascii')
                                data_uri = f"data:image/jpeg;base64,{img_b64}"
                                
                                # Create IMG tag
                                img_tag = new_soup.new_tag("img")
                                img_tag['src'] = data_uri
                                img_tag['style'] = "display: block; margin: 10px auto; max-width: 100%;"
                                
                                # Replace div with img
                                m_div.replace_with(img_tag)
                                print("DEBUG: Mermaid render successful.")
                            else:
                                print(f"DEBUG: Mermaid render failed: {response.status_code}")
                                # Fallback to code block (already styled by CSS)
                        except Exception as me:
                             print(f"DEBUG: Mermaid rendering exception: {me}")
                             # Fallback
                except Exception as e:
                    print(f"DEBUG: Mermaid setup failed: {e}")

                
                # Remove any screen-only elements: Nav, Sidebar, Buttons
                # Extended list based on view.html
                screen_only_selectors = [
                    'script', 'button', 'nav', 
                    '.top-nav', '.toc-sidebar', '.edit-actions', 
                    '.btn', '.no-print'
                ]
                for selector in screen_only_selectors:
                    # Handle tag names vs classes
                    if selector.startswith('.'):
                        for el in body.find_all(class_=selector[1:]):
                            el.decompose()
                    else:
                        for el in body.find_all(selector):
                            el.decompose()

                # Update content to be just this clean structure
                content_html = str(new_soup)
            else:
                 logger.warning("PDFExport: Could not find content container (#documentContent, .markdown-content, or .content-area)")
                 # Even if extracting container fails, we should try to strip sidebar/nav from the FULL soup
                 # Fallback cleanup on the original soup
                 for selector in ['.top-nav', '.toc-sidebar', '.edit-actions', 'nav', 'script', 'button']:
                     if selector.startswith('.'):
                         for el in soup.find_all(class_=selector[1:]):
                             el.decompose()
                     else:
                         for el in soup.find_all(selector):
                             el.decompose()
                 content_html = str(soup)

        except Exception as e:
            logger.error(f"PDFExport: preprocessing failed: {e}")
            logger.error(traceback.format_exc())
            pass


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
        # Note: We use plain string concatenation to avoid f-string curly brace escaping issues
        
        pdf_css = """
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: Helvetica, Arial, sans-serif;
                    font-size: 10pt;
                    color: #000000;
                    background-color: #ffffff;
                }
                p {
                    margin-bottom: 10px;
                    line-height: 1.5; /* Vital for inline emojis to not clip */
                }
                /* Force simplified styling for PDF */
                .markdown-body { font-family: Helvetica, Arial, sans-serif !important; color: black !important; background: white !important; }
                
                /* Smart Page Breaks (Refined) */
                h1, h2, h3, h4, h5, h6 { 
                    color: #333 !important; 
                    page-break-after: avoid; /* Keep with next paragraph */
                }
                
                /* Only strictly keep small visuals together. Allow text/tables to break. */
                img, figure { 
                    page-break-inside: avoid; 
                }
                
                /* Mermaid Diagrams: Render as styled code blocks since we cannot render JS to SVG */
                .mermaid {
                    font-family: 'Courier New', Courier, monospace;
                    white-space: pre-wrap;
                    background-color: #f8f8f8;
                    border: 1px solid #e1e4e8;
                    border-radius: 4px;
                    padding: 10px;
                    margin: 10px 0;
                    color: #555;
                    font-size: 8pt;
                    display: block;
                    page-break-inside: avoid;
                }
                
                h1 { border-bottom: 2px solid #333; padding-bottom: 5px; }

                /* Abbreviations */
                abbr { text-decoration: none; border-bottom: 1px dotted #666; cursor: help; }
                
                /* Definition Lists */
                dl { margin-bottom: 15px; }
                dt { font-weight: bold; margin-top: 10px; }
                dd { margin-left: 20px; margin-bottom: 5px; }

                code, pre { font-family: Courier; background: #f5f5f5; border: 1px solid #eee; }
                table { border-collapse: collapse; width: 100%; margin-top: 10px; }
                td, th { border: 1px solid #ccc; padding: 6px; text-align: left; }
                th { background-color: #f3f4f6; font-weight: bold; }

                /* Document Header Styling (Title & Metadata) */
                .document-header { margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 10px; }
                .document-title { font-size: 24pt; font-weight: bold; margin: 0 0 10px 0; border: none !important; }
                .document-path { color: #666; font-size: 9pt; font-style: italic; }

                /* TOC Styling (Professional Print) */
                .toc-container {
                    background-color: transparent;
                    border: none;
                    padding: 0;
                    margin-bottom: 40px;
                    page-break-after: always;
                }
                .toc-header {
                    font-size: 14pt;
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    margin-bottom: 20px;
                    border-bottom: 3px solid #000;
                    padding-bottom: 10px;
                    color: #000;
                }
                .toc-content ul { list-style-type: none; padding-left: 0; }
                .toc-content li { margin-bottom: 8px; }
                
                /* Top Level Items */
                .toc-content > ul > li > a {
                    font-weight: bold;
                    font-size: 11pt;
                    color: #000;
                    text-decoration: none;
                }
                
                /* Nested Items */
                .toc-content ul ul { 
                    padding-left: 20px; 
                    margin-top: 4px;
                }
                .toc-content ul ul li a {
                    font-size: 10pt;
                    color: #555;
                    text-decoration: none;
                }

                /* --- ALERTS / ADMONITIONS --- */
                /* Base Admonition */
                .admonition {
                    border: 1px solid #e1e4e8;
                    border-left: 5px solid #0969da; /* Default Blue */
                    background-color: #f8f8f8;
                    padding: 10px;
                    margin: 15px 0;
                    border-radius: 4px;
                    page-break-inside: avoid;
                }
                .admonition-title {
                    font-weight: bold;
                    display: block;
                    margin-top: 0;
                    margin-bottom: 5px;
                    color: #24292e;
                }
                
                /* Specific Types */
                .admonition.note { border-left-color: #0969da; background-color: #f0f6fc; }
                .admonition.tip { border-left-color: #1a7f37; background-color: #f0fff4; }
                .admonition.important { border-left-color: #8250df; background-color: #f3f0ff; }
                .admonition.warning { border-left-color: #9a6700; background-color: #fff8c5; }
                .admonition.caution { border-left-color: #d1242f; background-color: #ffebe9; }

                /* GitHub Alerts (Converted to Tables for PDF Stability) */
                .alert-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 16px;
                    page-break-inside: avoid;
                    background-color: transparent; /* Vital: Don't double paint */
                }
                
                tr { page-break-inside: avoid; }

                .alert-cell {
                    border-left: 5px solid #0969da; /* Default Blue */
                    padding: 10px;
                    background-color: #f8f8f8;
                    vertical-align: top;
                    page-break-inside: avoid;
                }
                
                .markdown-alert-title { 
                    font-weight: bold; 
                    margin-top: 0;
                    margin-bottom: 5px;
                    color: #24292e; 
                }
                
                /* COLLAPSE MARGINS */
                .alert-cell p {
                    margin-top: 0;
                    margin-bottom: 10px;
                    background-color: transparent;
                }
                .alert-cell p:last-child {
                    margin-bottom: 0;
                }
                
                /* Specific Alert Colors (Applied to the Cell Border & Background) */
                table.markdown-alert-note .alert-cell { border-left-color: #0969da; background-color: #f0f6fc; }
                table.markdown-alert-tip .alert-cell { border-left-color: #1a7f37; background-color: #f0fff4; }
                table.markdown-alert-important .alert-cell { border-left-color: #8250df; background-color: #f3f0ff; }
                table.markdown-alert-warning .alert-cell { border-left-color: #9a6700; background-color: #fff8c5; }
                table.markdown-alert-caution .alert-cell { border-left-color: #d1242f; background-color: #ffebe9; }

                /* --- HIGHLIGHT --- */
                mark {
                    background-color: #fffac1;
                    color: #333;
                    padding: 0 2px;
                    border-radius: 2px;
                }

                /* --- EMOJIS --- */
                /* Constrain size to prevent massive rendering */
                .emoji, span.emoji {
                    font-size: 1.0em;
                    vertical-align: text-bottom;
                    font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif;
                }
                
                /* WikiLinks */
                a.wikilink { color: #0969da; text-decoration: none; }

                /* --- CODE HIGHLIGHTING (Pygments/Prism) --- */
                .highlight pre, pre.highlight {
                    background-color: #f6f8fa;
                    border: 1px solid #e1e4e8;
                    border-radius: 3px;
                    padding: 10px;
                    overflow-x: auto;
                    line-height: 1.45;
                    font-size: 9pt;
                }
                .highlight .hll { background-color: #ffffcc } /* Highlighted line */
                .highlight .c { color: #6a737d } /* Comment */
                .highlight .err { color: #b31d28 } /* Error */
                .highlight .k { color: #d73a49 } /* Keyword */
                .highlight .l { color: #005cc5 } /* Literal */
                .highlight .n { color: #24292e } /* Name */
                .highlight .o { color: #d73a49 } /* Operator */
                .highlight .p { color: #24292e } /* Punctuation */
                .highlight .cm { color: #6a737d } /* Comment.Multiline */
                .highlight .cp { color: #6a737d } /* Comment.Preproc */
                .highlight .c1 { color: #6a737d } /* Comment.Single */
                .highlight .cs { color: #6a737d } /* Comment.Special */
                .highlight .gd { color: #b31d28 } /* Generic.Deleted */
                .highlight .ge { font-style: italic } /* Generic.Emph */
                .highlight .gr { color: #b31d28 } /* Generic.Error */
                .highlight .gh { color: #005cc5; font-weight: bold } /* Generic.Heading */
                .highlight .gi { color: #22863a } /* Generic.Inserted */
                .highlight .go { color: #6a737d } /* Generic.Output */
                .highlight .gp { color: #6a737d } /* Generic.Prompt */
                .highlight .gs { font-weight: bold } /* Generic.Strong */
                .highlight .gu { color: #005cc5; font-weight: bold } /* Generic.Subheading */
                .highlight .gt { color: #b31d28 } /* Generic.Traceback */
                .highlight .kc { color: #d73a49 } /* Keyword.Constant */
                .highlight .kd { color: #d73a49 } /* Keyword.Declaration */
                .highlight .kn { color: #d73a49 } /* Keyword.Namespace */
                .highlight .kp { color: #d73a49 } /* Keyword.Pseudo */
                .highlight .kr { color: #d73a49 } /* Keyword.Reserved */
                .highlight .kt { color: #d73a49 } /* Keyword.Type */
                .highlight .ld { color: #005cc5 } /* Literal.Date */
                .highlight .m { color: #005cc5 } /* Literal.Number */
                .highlight .s { color: #032f62 } /* Literal.String */
                .highlight .na { color: #6f42c1 } /* Name.Attribute */
                .highlight .nb { color: #24292e } /* Name.Builtin */
                .highlight .nc { color: #6f42c1 } /* Name.Class */
                .highlight .no { color: #005cc5 } /* Name.Constant */
                .highlight .nd { color: #6f42c1 } /* Name.Decorator */
                .highlight .ni { color: #24292e } /* Name.Entity */
                .highlight .ne { color: #b31d28 } /* Name.Exception */
                .highlight .nf { color: #6f42c1 } /* Name.Function */
                .highlight .nl { color: #24292e } /* Name.Label */
                .highlight .nn { color: #24292e } /* Name.Namespace */
                .highlight .nx { color: #56b4eb } /* Name.Other */
                .highlight .py { color: #24292e } /* Name.Property */
                .highlight .nt { color: #22863a } /* Name.Tag */
                .highlight .nv { color: #005cc5 } /* Name.Variable */
                .highlight .ow { color: #d73a49 } /* Operator.Word */
                .highlight .w { color: #eff2f7 } /* Text.Whitespace */
                .highlight .mf { color: #005cc5 } /* Literal.Number.Float */
                .highlight .mh { color: #005cc5 } /* Literal.Number.Hex */
                .highlight .mi { color: #005cc5 } /* Literal.Number.Integer */
                .highlight .mo { color: #005cc5 } /* Literal.Number.Oct */
                .highlight .sb { color: #032f62 } /* Literal.String.Backtick */
                .highlight .sc { color: #032f62 } /* Literal.String.Char */
                .highlight .sd { color: #032f62 } /* Literal.String.Doc */
                .highlight .s2 { color: #032f62 } /* Literal.String.Double */
                .highlight .se { color: #032f62 } /* Literal.String.Escape */
                .highlight .sh { color: #032f62 } /* Literal.String.Heredoc */
                .highlight .si { color: #032f62 } /* Literal.String.Interpol */
                .highlight .sx { color: #032f62 } /* Literal.String.Other */
                .highlight .sr { color: #032f62 } /* Literal.String.Regex */
                .highlight .s1 { color: #032f62 } /* Literal.String.Single */
                .highlight .ss { color: #032f62 } /* Literal.String.Symbol */
                .highlight .bp { color: #24292e } /* Name.Builtin.Pseudo */
                .highlight .vc { color: #005cc5 } /* Name.Variable.Class */
                .highlight .vg { color: #005cc5 } /* Name.Variable.Global */
                .highlight .vi { color: #005cc5 } /* Name.Variable.Instance */
                .highlight .il { color: #005cc5 } /* Literal.Number.Integer.Long */

                /* --- TABS --- */
                .tab-container {
                    margin: 15px 0;
                    border: 1px solid #e1e4e8;
                    border-radius: 4px;
                    page-break-inside: avoid;
                }
                .tab-headers {
                    display: flex;
                    border-bottom: 1px solid #e1e4e8;
                    background-color: #f6f8fa;
                    padding: 5px 10px;
                }
                .tab-header {
                    padding: 8px 15px;
                    cursor: pointer;
                    font-weight: bold;
                    color: #586069;
                    border-right: 1px solid #e1e4e8;
                }
                .tab-header:last-child { border-right: none; }
                .tab-header.active {
                    background-color: #ffffff;
                    color: #24292e;
                    border-bottom: 2px solid #0366d6;
                    margin-bottom: -1px;
                }
                .tab-content {
                    padding: 15px;
                    background-color: #ffffff;
                }
                
                /* --- FOOTNOTES --- */
                div.footnote {
                    font-size: 0.9em;
                    color: #555;
                    margin-top: 20px; /* Restore original spacing */
                    border-top: none; 
                    padding: 0;
                    margin-left: 0;
                }
                div.footnote hr {
                    border: 0;
                    border-top: 1px solid #ddd;
                    margin: 0 0 10px 0; /* consistent gap below line */
                    width: 100%;
                }
                div.footnote table.footnote-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 0; 
                    margin-left: 0; 
                    margin-right: 0;
                    border: none !important; /* Force override global styles */
                }
                div.footnote table.footnote-table td {
                    border: none !important; /* Force override global styles */
                    padding: 0;
                }
                div.footnote td.fn-num {
                    /* Width handled by HTML attribute */
                    white-space: nowrap; 
                    padding: 0;
                    padding-right: 10px !important; /* Increased gap per user request */
                    color: #2563eb;
                    font-weight: bold;
                    font-size: 0.8em;
                    vertical-align: top;
                }
                div.footnote td.fn-content {
                    vertical-align: top;
                    text-align: left;
                    padding: 0;
                    margin: 0;
                    color: #333;
                    font-size: 0.9em;
                }
                /* Ensure paragraphs inside footnotes don't add massive gaps */
                div.footnote td.fn-content p {
                    margin-top: 0;
                    margin-bottom: 5px;
                }
        """


        full_html = """
        <html>
        <head>
            <style>
            {}
            </style>
        </head>
        <body>
            <div class="markdown-body">
                {}
            </div>
        </body>
        </html>
        """.format(pdf_css, content_html)
        
        # 5. Convert to PDF using Safe Methods
        
        # Convert to PDF in memory
        result = io.BytesIO()
        
        pisa_status = pisa.CreatePDF(
            full_html,              # the HTML to convert
            dest=result             # file handle to recieve result
        )
            
        if pisa_status.err:
            raise RuntimeError(f"PDF generation error: {pisa_status.err}")
            
        logger.info(f"PDFExport: Generated {result.getbuffer().nbytes} bytes.")
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


PLUGIN_METADATA = {
    'name': 'PDF Export',
    'description': 'Converts documentation to professional PDF format with Table of Contents, cover page, and optimized print layout.',
    'category': 'export',
    'icon': 'fa-file-pdf',
    'preinstalled': False
}


