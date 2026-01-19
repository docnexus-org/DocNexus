
import sys
import os
import io
import re
from bs4 import BeautifulSoup

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import plugin logic
from docnexus.plugins.word_export.plugin import transform_html_for_word
import logging

# Configure logging to show info (to see our debug prints)
logging.basicConfig(level=logging.INFO)

def test_word_rendering_components():
    print("==================================================")
    print("TEST: Word Rendering Components (Math, Tabs, Emojis)")
    print("==================================================")

    html_input = """
    <div class="markdown-content" id="documentContent">
        <h1>Comprehensive Word Test</h1>
        
        <!-- 1. Math Test (Standard Arithmatex output) -->
        <h3>Math Formulas</h3>
        <p>Inline: <div class="arithmatex"><script type="math/tex">E=mc^2</script></div></p>
        <p>Block:</p>
        <div class="arithmatex">
            <script type="math/tex; mode=display">\\frac{n!}{k!(n-k)!} = \\binom{n}{k}</script>
        </div>
        
        <!-- 2. Emoji Test (Bracket Issue) -->
        <h3>Emojis</h3>
        <p>Rocket: <img class="emoji" alt=":rocket:" src="rocket.png"></p>

        <!-- 3. Tabbed Interface Test (Merged Text Issue) -->
        <h3>Tabbed Interface</h3>
        <div class="tabbed-set" data-tabs="1:2">
            <input checked="checked" id="__tabbed_1_1" name="__tabbed_1" type="radio">
            <label for="__tabbed_1_1">Python</label>
            <div class="tabbed-content">
                <p>print("Hello")</p>
            </div>
            
            <input id="__tabbed_1_2" name="__tabbed_1" type="radio">
            <label for="__tabbed_1_2">JavaScript</label>
            <div class="tabbed-content">
                <p>console.log("Hello")</p>
            </div>
        </div>

    </div>
    """

    soup = BeautifulSoup(html_input, 'html.parser')
    
    print("\n[INFO] Transforming HTML...")
    transform_html_for_word(soup)
    output_html = str(soup)
    
    # --- Validations ---
    print("\n[INFO] Validating Output...")
    errors = []

    # 1. Math Validation
    if "<img" not in output_html or "latex.codecogs.com" not in output_html:
        errors.append("Math: No CodeCogs image generated.")
    
    if "E=mc" in output_html and "<img" not in output_html:
        errors.append("Math: Raw TeX visible without image replacement.")
        
    # Garbage Text Check
    if "n!k!" in output_html: 
        # Wait, the TeX is n!k!... in alt text or raw?
        # If it's in ALT attribute of IMG, that's fine.
        # If it's raw text outside tags, that's bad.
        # Let's check if it's strictly inside alt="..."
        # Simple regex check for text content outside tags
        text_content = soup.get_text()
        if "n!k!(n-k)!" in text_content:
             # It might be in the alt text which get_text() might ignore? No, get_text returns string.
             # Actually, get_text() normally ignores attributes.
             # So if we see it in get_text(), it means it's visible text -> FAIL.
             errors.append("Math: Garbage text (n!k!...) detected in visible text content.")

    # 2. Emoji Validation
    # We want to ensure NO brackets around the emoji or alt text
    if "[:rocket:]" in output_html or "[rocket]" in output_html:
         errors.append("Emoji: Brackets [] detected around emoji.")
         
    # 3. Tabbed Interface Validation
    # Should be flattened. Headers should be visible. Inputs should be gone.
    if "<input" in output_html:
        errors.append("Tabs: Raw <input> tags remaining.")
    
    if "Python" not in output_html or "JavaScript" not in output_html:
        errors.append("Tabs: Tab labels lost.")
        
    # Check for merging (hard to do strictly with regex strings, but we can check adjacent text)
    # The fix ensures "Python" is wrapped in a header/strong tag usually.
    # Check if "Python" and "print" are separated.
    
    if errors:
        print("\n[FAIL] Errors found:")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All Word Component tests passed.")

if __name__ == "__main__":
    test_word_rendering_components()
