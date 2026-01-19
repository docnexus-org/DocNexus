from PIL import Image, ImageDraw, ImageFont
import os

def test_render_emoji(char, filename):
    try:
        # Windows 10/11 Emoji Font
        font_path = "C:/Windows/Fonts/seguiemj.ttf"
        if not os.path.exists(font_path):
             # Try fallback or standard
             font_path = "arial.ttf" 
        
        # Color support in PIL (ImageFont.Layout) requires libraqm usually, 
        # but basic TTF rendering might just give outline if it's not COLR supported.
        # Actually standard Pillow 10+ supports COLR/CPAL? Let's verify.
        
        font_size = 64
        font = ImageFont.truetype(font_path, font_size)
        
        # Create image
        img = Image.new('RGBA', (70, 70), (0, 0, 0, 0)) # Transparent
        draw = ImageDraw.Draw(img)
        
        # Draw emoji
        # Embedded color bitmaps (SBIX/CBDT) or Vector (COLR) support in Pillow is tricky.
        # Often it renders black and white outline for complex fonts if libraqm/harfbuzz isn't perfect.
        # But even a B&W rendered bitmap is better than a clipped PDF font.
        # 'embedded_color=True' was added in recent Pillow versions for some fonts.
        
        draw.text((3, 3), char, font=font, fill="black", embedded_color=True) 
        
        img.save(filename)
        print(f"Saved {filename}")
        
    except Exception as e:
        print(f"Error rendering emoji: {e}")

if __name__ == "__main__":
    test_render_emoji("🚀", "test_rocket.png")
    test_render_emoji("🎉", "test_tada.png")
