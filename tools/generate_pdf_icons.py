import base64
import io
from PIL import Image, ImageDraw, ImageFont

def create_base64_icon(color, text, shape='circle'):
    size = 32
    img = Image.new('RGBA', (size, size), (255, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw Shape
    padding = 2
    if shape == 'circle':
        draw.ellipse([padding, padding, size-padding, size-padding], fill=color)
    elif shape == 'triangle':
        # Triangle pointing up
        points = [
            (size//2, padding), 
            (padding, size-padding), 
            (size-padding, size-padding)
        ]
        draw.polygon(points, fill=color)
    elif shape == 'octagon':
        # Simple box approximation or octagon
        # Let's do rounded rect or just circle for caution is fine too, but let's try octagon
        p = padding
        s = size - padding
        m = size // 3
        points = [
            (m, p), (size-m, p),
            (s, m), (s, size-m),
            (size-m, s), (m, s),
            (p, size-m), (p, m)
        ]
        draw.polygon(points, fill=color)
        
    # Draw Text
    # Load basic font or default
    try:
        # Try to load Arial or similar
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Centering text (approximate) - getbbox is better but simple w/h subtraction works for basic
    text_bbox = draw.textbbox((0,0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    
    x = (size - text_w) / 2
    y = (size - text_h) / 2 - 2 # slight adjust up
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save to buffer
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

icons = {
    'note': create_base64_icon('#0969da', 'i', 'circle'),
    'tip': create_base64_icon('#1a7f37', '?', 'circle'),
    'important': create_base64_icon('#8250df', '!', 'circle'),
    'warning': create_base64_icon('#9a6700', '!', 'triangle'),
    'caution': create_base64_icon('#d1242f', 'X', 'octagon')
}

with open('tools/icon_data.txt', 'w') as f:
    f.write("ICON_MAP = {\n")
    for k, v in icons.items():
        f.write(f"    '{k}': 'data:image/png;base64,{v}',\n")
    f.write("}\n")
