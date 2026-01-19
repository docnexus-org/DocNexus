
import sys
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docnexus.plugins.pdf_export.plugin import export_pdf

def get_emoji_base64(char):
    # Simplified standalone version for testing
    from PIL import Image, ImageDraw, ImageFont
    import io
    import base64
    
    # Create 64x64 White BG JPEG (Same as plugin)
    img = Image.new('RGB', (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = None
        
    # Draw simple rect or text
    draw.rectangle([10, 10, 54, 54], fill="red")
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8').replace('\n', '')
    return "data:image/jpeg;base64," + b64_str

try:
    from pypdf import PdfReader
except ImportError:
    print("Please install pypdf: pip install pypdf")
    sys.exit(1)

def generate_test_html(img_tag_html, ref_src):
    return f"""
    <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 10pt; }}
            </style>
        </head>
        <body>
            <div id="documentContent"> <!-- Satisfy Plugin Finder -->
                <h3>Emoji Tuning Test</h3>
                <p>
                    Start text [ {img_tag_html} ] End text.
                </p>
                <p>
                    Reference: <img src="{ref_src}" style="width:16px;height:16px;" width="16" height="16">
                </p>
            </div>
        </body>
    </html>
    """

def analyze_pdf(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    page = reader.pages[0]
    count = 0
    
    if '/Resources' in page and '/XObject' in page['/Resources']:
        x_objects = page['/Resources']['/XObject'].get_object()
        for obj in x_objects:
            if x_objects[obj]['/Subtype'] == '/Image':
                count += 1
                # print(f"  Found Image: {obj}")
    return count

def run_tests():
    # Helper to get unique b64
    def get_b64(char, color):
        from PIL import Image, ImageDraw, ImageFont
        import io, base64
        img = Image.new('RGB', (64, 64), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 54, 54], fill=color)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=95)
        return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode('utf-8').replace('\n', '')

    # Generate UniqueSrc for Test (Red) and Reference (Blue)
    test_src = get_b64("T", "red")
    ref_src = get_b64("R", "blue")
    
    # Alert Icon (Shortened for brevity but valid)
    # The Note icon from plugin.py
    alert_png = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABgElEQVR4nO2bu03EQBRF7xxthEROBVSwrdAAGX3QAzExrRATkJHQANIGJEZCAlkr7/o3X989kgNb9nv3jt/Y45EndPIGmbPLmezq4X1ywR2eboMyELpKDJdqkNBVbjx1Q4SuAdMpG4NWzcfKG7oGjcesBrZgfo0eciZLzRJd5EiSk7n6SBm8FHN0kiJoDUzVS8xgtTFFNzGC1MyYftZc3ArnfCBz2PrdH/PDnJNbZ8gXMgeZE7pC5X+3v9bz/c3//v7xQ2+f39m/HJE5ODz8jun7RObsSiV+ef363UqDzMGt/x/7RebsSiUuOQ7og8xB5iBzkDnIHGQOMgeZQ+5/cmrhzy8yB5mDzKG/4/IcuEyKnusCh41XwbE/ZA4yh6GDW+0GQ76Yc3LLnPKDzAljc+FbmC4/V82subgFxvQTI0itTNFNzGA1MVUvKYKWZo5OUgYvwVx95EiSiyW6yJksJUv1hBgv+ZJjhbU3ghpElMwbLusGlQ7blaOnsFs7rAb4AedJsUM6zwafAAAAAElFTkSuQmCC'

    # Define Configurations to Test
    configs = [
        {
            "name": "Alert PNG Inline",
            "html": f'<img src="{alert_png}" style="width: 16px; height: 16px; vertical-align: middle;">'
        },
        {
            "name": "My JPEG Inline",
            "html": f'<img src="{test_src}" style="width: 16px; height: 16px; vertical-align: middle;">'
        },
        {
            "name": "Alert PNG in Bold Wrapper",
            "html": f'<b><img src="{alert_png}" style="width: 16px; height: 16px; vertical-align: middle;"></b>'
        },
         {
            "name": "Emoji in Bold Wrapper (JPEG)",
            "html": f'<b><img src="{test_src}" style="width: 16px; height: 16px; vertical-align: middle;"></b>'
        }
    ]
    
    print(f"--- Starting Programmatic Tuning Loop ---")
    
    for i, config in enumerate(configs):
        print(f"\nRunning Config {i+1}/{len(configs)}: {config['name']}")
        html = generate_test_html(config['html'], ref_src)
        
        try:
            pdf_bytes = export_pdf(html)
            
            # Analyze
            img_count = analyze_pdf(pdf_bytes)
            
            # Expect 2 if both valid. 1 if only Ref. 0 if none.
            status = "FAIL"
            if img_count == 2: status = "PASS (Both Present)"
            elif img_count == 1: status = "PARTIAL (One Missing)"
            else: status = "FAIL (None Found)"
            
            print(f"  Result: {status} (XObjects: {img_count})")
                    
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_tests()
