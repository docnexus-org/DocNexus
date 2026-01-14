import base64
import io
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_base64_icon(color, text, shape='circle'):
    size = 64 # High res for PDF
    img = Image.new('RGBA', (size, size), (255, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    padding = 2
    if shape == 'circle':
        draw.ellipse([padding, padding, size-padding, size-padding], fill=color)
    elif shape == 'triangle':
        points = [(size//2, padding), (padding, size-padding), (size-padding, size-padding)]
        draw.polygon(points, fill=color)
    elif shape == 'octagon':
        # Simple box for caution
        draw.rectangle([padding, padding, size-padding, size-padding], fill=color)
        
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    text_bbox = draw.textbbox((0,0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    x = (size - text_w) / 2
    y = (size - text_h) / 2 - 4
    
    draw.text((x, y), text, fill='white', font=font)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

# Generate Icons
icon_data = {
    'note': create_base64_icon('#0969da', 'i', 'circle'),
    'tip': create_base64_icon('#1a7f37', '?', 'circle'),
    'important': create_base64_icon('#8250df', '!', 'circle'),
    'warning': create_base64_icon('#9a6700', '!', 'triangle'),
    'caution': create_base64_icon('#d1242f', 'X', 'octagon')
}

# Add fallback mappings
icon_map_str = "        alert_icons = {\n"
for k, v in icon_data.items():
    icon_map_str += f"            '{k}': 'data:image/png;base64,{v}',\n"

# Add legacy mappings pointing to same base64
for k in icon_data.keys():
    icon_map_str += f"            'markdown-alert-{k}': 'data:image/png;base64,{icon_data[k]}',\n"
icon_map_str += "        }"

# Patch File
plugin_path = Path("docnexus/plugins/pdf_export/plugin.py")
content = plugin_path.read_text(encoding='utf-8')

# Regex to find the alert_icons block
# Matches alert_icons = { ... } considering indented execution
pattern = r"alert_icons = \{[^\}]+\}"
new_content = re.sub(pattern, icon_map_str.strip(), content, flags=re.DOTALL)

if content == new_content:
    print("No replacement made! Check regex.")
else:
    plugin_path.write_text(new_content, encoding='utf-8')
    print("Successfully patched plugin.py with Base64 icons.")
