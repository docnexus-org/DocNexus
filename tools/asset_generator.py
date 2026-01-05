from PIL import Image
import os

# Configuration
SOURCE_LOGO = r"d:\Code\DocNexus\docs\assets\docnexus_logo.png"
STATIC_DIR = r"d:\Code\DocNexus\docnexus\static"
DOCS_ASSETS_DIR = r"d:\Code\DocNexus\docs\assets"

def generate_assets():
    if not os.path.exists(SOURCE_LOGO):
        print(f"Error: Source logo not found at {SOURCE_LOGO}")
        # Fallback to check if user meant one of the v3 ones if rename didn't happen
        # But user said "This is the logo I have finalised... @[.../docnexus_logo.png]"
        # I will assume it exists.
        return

    img = Image.open(SOURCE_LOGO)
    
    # 1. Web Logo (High quality, sensible height for headers)
    # Usually headers vary, but keeping a 512px width master for web usage is good
    web_logo = img.copy()
    web_logo.thumbnail((512, 512))
    web_logo.save(os.path.join(STATIC_DIR, "logo.png"), "PNG")
    print("Generated web logo: static/logo.png")

    # 2. Favicon (Multi-size ICO)
    # Sizes: 16, 32, 48, 64, 128, 256
    icon_sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    img.save(os.path.join(STATIC_DIR, "logo.ico"), format='ICO', sizes=icon_sizes)
    print("Generated favicon: static/logo.ico (multi-size)")

    # 3. Exe Icon (Same ICO usually works, but specific for build)
    # PyInstaller uses the .ico file. We can copy it to project root or use the static one.
    # Just to be safe for 'make.ps1' or 'pyinstaller', let's ensure a 'logo.ico' is in project root if needed
    # But usually it pulls from static or a specific path. 
    # Current make.ps1 or spec might use 'docnexus.ico' or similar. 
    # I'll save a copy to docs/assets/app_icon.ico for clarity.
    img.save(os.path.join(DOCS_ASSETS_DIR, "app_icon.ico"), format='ICO', sizes=icon_sizes)
    print("Generated exe icon: docs/assets/app_icon.ico")

    # 4. Letterhead Logo (High Res, 300 DPI equivalent roughly)
    # 8K is already huge. Let's make a crisp 2000px version for docs.
    letterhead = img.copy()
    letterhead.thumbnail((2000, 2000))
    letterhead.save(os.path.join(DOCS_ASSETS_DIR, "logo_letterhead.png"), "PNG")
    print("Generated letterhead logo: docs/assets/logo_letterhead.png")

if __name__ == "__main__":
    generate_assets()
