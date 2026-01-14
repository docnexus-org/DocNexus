
import sys
import os
import io

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docnexus.plugins.pdf_export.plugin import transform_html_for_pdf, export_pdf
from bs4 import BeautifulSoup
from xhtml2pdf import pisa

def test_generate_alert_pdf():
    html_content = """
    <h1>Alert Test</h1>
    
    <div class="markdown-alert markdown-alert-note">
        <p class="markdown-alert-title">Note</p>
        <p>This is a standard note alert.</p>
        <p>It has multiple paragraphs.</p>
    </div>

    <div class="markdown-alert markdown-alert-warning">
        <p class="markdown-alert-title">Warning</p>
        <p>This is a warning alert.</p>
    </div>
    
    <br><hr><br>
    
    <!-- Scenario 2: Standard Admonition (what renderer.py produces) -->
    <div class="admonition note">
        <p class="admonition-title">Real Note</p>
        <p>This is a standard admonition note produced by the renderer.</p>
        <p>It should also be flattened.</p>
    </div>
    """
    
    output_filename = "test_alert_output.pdf"
    
    # We can't easily invoke export_pdf directly because it does file I/O and imports other things.
    # But we can verify the transformation logic first.
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Run transformation
    transform_html_for_pdf(soup)
    
    print("--- Transformed HTML ---")
    print(soup.prettify())
    
    # Now let's try to generate a PDF snippet using xhtml2pdf to see if it crashes or works
    # We will use a simplified CSS here designed to mimic the plugin
    
    css = """
    @page { size: A4; margin: 2cm; }
    body { font-family: Helvetica; }
    
    /* Simplified CSS for Flattened Tables */
    table.alert-table { width: 100%; border-collapse: collapse; margin-bottom: 16px; background-color: transparent; border: 0;}
    td.alert-cell { border-left: 5px solid #0969da; padding: 10px; background-color: #f0f6fc; vertical-align: top; }
    
    /* No P styles needed */
    """
    
    full_html = f"<html><head><style>{css}</style></head><body>{str(soup)}</body></html>"
    
    with open(output_filename, "wb") as f:
        pisa_status = pisa.CreatePDF(full_html, dest=f)
    
    if pisa_status.err:
        print("PDF Gen Failed")
    else:
        print(f"PDF Gen Success: {output_filename}")

if __name__ == "__main__":
    test_generate_alert_pdf()
