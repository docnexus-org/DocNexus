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

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# PDF Transformation Logic
# -------------------------------------------------------------------------
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
        for link in soup.find_all('a', href=True):
            href = link['href']
            # If it's a relative link (no http/https) and looks like a file/slug
            if not href.startswith(('http:', 'https:', 'mailto:', '#', 'data:')):
                # Convert to internal anchor reference
                # Example: "feature_test_v1.2.6" -> "#feature_test_v1.2.6"
                # But ID matching is tricky. Simple slugify might be needed or assuming loose match.
                # Use a safe heuristic: if it doesn't look like a filename with extension (unless .md), treat as TOC target
                if not '.' in href or href.endswith('.md'):
                    target_id = href.replace('.md', '').replace('.', '').replace(' ', '-')
                    link['href'] = f"#{target_id}"
                    link.attrs['pdf-converted-link'] = "true"

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

        # 5. Wrap Emojis in <span> for sizing control
        # Regex for common emoji ranges (Surrogates, Dingbats, Emoticons, Symbols)
        emoji_pattern = re.compile(
            r'[\U00010000-\U0010ffff]'  # SMP (contains most emojis)
            r'|[\u2600-\u27ff]'         # Misc Symbols
            r'|[\u2300-\u23ff]'         # Misc Technical
            r'|[\u2b50]'                # Star
            r'|[\u203c-\u2049]'         # Punctuation (!!, !?, etc)
        )
        
        # Traverse text nodes to wrap emojis
        for text_node in soup.find_all(string=True):
            if text_node.parent.name in ['script', 'style', 'pre', 'code', 'span', 'div'] and 'emoji' in (text_node.parent.get('class') or []):
                continue
            
            text = str(text_node)
            if emoji_pattern.search(text):
                # Replace emoji with span wrapped version
                new_html = emoji_pattern.sub(r'<span class="emoji">\g<0></span>', text)
                # Parse back to nodes
                new_nodes = BeautifulSoup(new_html, 'html.parser')
                text_node.replace_with(new_nodes)

        # 6. Transform Math (KaTeX/MathJax) -> Clean TeX
        for katex_node in soup.find_all(class_='katex'):
            try:
                annotation = katex_node.find('annotation', attrs={'encoding': 'application/x-tex'})
                if annotation:
                    tex_code = annotation.get_text().strip()
                    is_block = False
                    parent = katex_node.parent
                    if parent and 'katex-display' in (parent.get('class') or []):
                        is_block = True
                    
                    new_node = soup.new_tag('div' if is_block else 'span')
                    if is_block:
                        new_node.string = f"$$ {tex_code} $$"
                        new_node['style'] = "display: block; margin: 10px 0; font-family: Courier; color: #333; background: #f5f5f5; padding: 5px;"
                    else:
                        new_node.string = f" ${tex_code}$ "
                        new_node['style'] = "font-family: Courier; color: #333;"
                    
                    # Replace logic
                    root_node = katex_node
                    if parent and 'arithmatex' in (parent.get('class') or []):
                        root_node = parent
                    elif parent and parent.name == 'span' and 'katex-display' in (parent.get('class') or []):
                            grandparent = parent.parent
                            if grandparent and 'arithmatex' in (grandparent.get('class') or []):
                                root_node = grandparent
                            else:
                                root_node = parent
                    root_node.replace_with(new_node)
                    continue
            except Exception:
                pass



        # Legacy MathJax Fallback
        for script in soup.find_all('script', type='math/tex'):
            tex = script.get_text()
            new_span = factory_soup.new_tag('span')
            new_span.string = f"${tex}$"
            script.replace_with(new_span)
            
        # Remove Preview/Dummy spans
        for junk in soup.find_all(class_=['MathJax_Preview', 'katex-html']):
            if junk: junk.decompose()

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

                # Create a fresh clean DOM
                new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
                body = new_soup.body
                
                # Append the main container
                body.append(main_container)
                
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
                /* Force simplified styling for PDF */
                .markdown-body { font-family: Helvetica, Arial, sans-serif !important; color: black !important; background: white !important; }
                
                /* Smart Page Breaks (Refined) */
                h1, h2, h3, h4, h5, h6 { 
                    color: #333 !important; 
                    page-break-after: avoid; /* Keep with next paragraph */
                }
                
                /* Only strictly keep small visuals together. Allow text/tables to break. */
                .mermaid, img, figure { 
                    page-break-inside: avoid; 
                }
                
                /* Removed aggressive h1 page-break-before to prevent blank pages */
                h1 { border-bottom: 2px solid #333; padding-bottom: 5px; }
                
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

# Metadata
PLUGIN_METADATA = {
    'name': 'PDF Export',
    'description': 'Converts documentation to professional PDF format with Table of Contents, cover page, and optimized print layout.',
    'category': 'export',
    'icon': 'fa-file-pdf',
    'preinstalled': False
}
