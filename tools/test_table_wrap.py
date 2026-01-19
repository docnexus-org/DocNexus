
import sys
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from docnexus.plugins.pdf_export.plugin import export_pdf

def get_test_image():
    # 64x64 Canvas, Glyph fills 50x50 centered
    img = Image.new('RGB', (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0,0,63,63], outline="red") # Border
    draw.rectangle([7,7,56,56], fill="blue")   # Glyph
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode('utf-8').replace('\n', '')

def run():
    img_src = get_test_image()
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; font-size: 10pt; }}
            p {{ margin-bottom: 10px; border: 1px dashed #ccc; }}
            table {{ width: 100%; border-collapse: collapse; }}
            td {{ border: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <h3>Layout Context Test</h3>
        
        <p>
            1. Standard Paragraph: Hello <img src="{img_src}" style="width:16px; height:16px; vertical-align: middle;"> World.
        </p>
        
        <table style="width: 100%;">
            <tr>
                <td>
                    2. Table Cell Wrapper: Hello <img src="{img_src}" style="width:16px; height:16px; vertical-align: middle;"> World.
                </td>
            </tr>
        </table>

        <div style="display: block; border: 1px solid blue; padding: 5px;">
             3. Div Wrapper: Hello <img src="{img_src}" style="width:16px; height:16px; vertical-align: middle;"> World.
        </div>
        
    </body>
    </html>
    """
    
    print("Generating test_table_wrap.pdf...")
    try:
        pdf_bytes = export_pdf(html)
        with open("test_table_wrap.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("Success: test_table_wrap.pdf created.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
