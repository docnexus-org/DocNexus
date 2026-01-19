
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.getcwd()))

import docnexus.core.renderer as renderer

def debug_renderer():
    text = "Emoji Test: :rocket: :tada: :snake: :heart:"
    print(f"Input: {text}")
    
    html, toc = renderer.render_baseline(text)
    
    print("\n--- Renderer Output (HTML) ---")
    print(html)
    print("------------------------------\n")
    
    # Analyze output for classes
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    imgs = soup.find_all('img')
    print(f"Found {len(imgs)} images.")
    for img in imgs:
        print(f"Image: {img}")
        print(f"Classes: {img.get('class')}")
        print(f"Alt: {img.get('alt')}")
        print(f"Src: {img.get('src')}")

if __name__ == "__main__":
    debug_renderer()
