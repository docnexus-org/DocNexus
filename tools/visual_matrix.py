
import sys
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from docnexus.plugins.pdf_export.plugin import export_pdf

# 1. Image Generator (Flexible Alignment)
def get_test_image(align_y="center"):
    # 64x64 Canvas
    img = Image.new('RGBA', (64, 64), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Draw a visible Square + Text
    # Color depends on alignment to identify it
    color = "red"
    if align_y == "top": color = "blue"
    if align_y == "bottom": color = "green"
    
    # Draw Glyphs
    # We draw a full box frame to see boundaries
    draw.rectangle([0,0,63,63], outline="black")
    
    # Draw filled block based on alignment intent
    # Glyph size 40x40
    if align_y == "center":
        draw.rectangle([12, 12, 52, 52], fill=color)
    elif align_y == "top":
        draw.rectangle([12, 0, 52, 40], fill=color) # Top aligned glyph
    
    # Save as PNG
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode('utf-8').replace('\n', '')

def generate_html():
    img_center = get_test_image("center")
    img_top = get_test_image("top")
    
    # CSS Styles to test
    styles = [
        ("Baseline (Default)", "vertical-align: baseline;"),
        ("Top", "vertical-align: top;"),
        ("Text-Top", "vertical-align: text-top;"),
        ("Middle", "vertical-align: middle;"),
        ("Bottom", "vertical-align: bottom;"),
        ("Text-Bottom", "vertical-align: text-bottom;"),
        ("Super", "vertical-align: super;"),
        ("Sub", "vertical-align: sub;")
    ]
    
    rows = []
    
    # 1. Standard Line Height
    rows.append("<h3>Group A: Standard Line Height</h3>")
    for name, style in styles:
        # We test both Centered Glyph and Top Glyph
        rows.append(f"""
        <p style="border-bottom: 1px dotted #ccc;">
            {name}: Text [ <img src="{img_center}" style="width:16px;height:16px;{style}"> ] 
            TopGlyph [ <img src="{img_top}" style="width:16px;height:16px;{style}"> ]
            Text
        </p>
        """)

    # 2. Increased Line Height
    rows.append("<h3>Group B: Line-Height 2.0</h3>")
    for name, style in styles:
        rows.append(f"""
        <p style="line-height: 2.0; border-bottom: 1px dotted #ccc;">
            {name}: Text [ <img src="{img_center}" style="width:16px;height:16px;{style}"> ] Text
        </p>
        """)

    return f"""
    <html>
    <head><style>body {{ font-family: Arial; }}</style></head>
    <body>
        <h2>Visual Alignment Matrix</h2>
        <div id="documentContent">
            {''.join(rows)}
        </div>
    </body>
    </html>
    """

def run():
    print("Generating visual_matrix.pdf...")
    html = generate_html()
    try:
        pdf_bytes = export_pdf(html)
        with open("visual_matrix.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("Success: visual_matrix.pdf created.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
