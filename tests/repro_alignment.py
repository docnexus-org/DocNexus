import sys
import os
from bs4 import BeautifulSoup

def test_list_detection():
    # Scenario 1: Tight List (likely Inline)
    # * Block: $$x^2$$
    html_tight = """
    <ul>
        <li>Block: <span class="arithmatex">\[ x^2 \]</span></li>
    </ul>
    """
    
    # Scenario 2: Loose List (likely Paragraphs)
    # * Block:
    # 
    #   $$x^2$$
    html_loose = """
    <ul>
        <li>
            <p>Block:</p>
            <div class="arithmatex">\[ x^2 \]</div>
        </li>
    </ul>
    """
    
    # Scenario 3: Broken List (Markdown often closes LI before block detection if indent is wrong)
    html_broken = """
    <ul>
        <li>Block:</li>
    </ul>
    <div class="arithmatex">\[ x^2 \]</div>
    """

    print("--- Testing Alignment Detection ---")
    
    for name, html in [("Tight", html_tight), ("Loose", html_loose), ("Broken", html_broken)]:
        soup = BeautifulSoup(html, "html.parser")
        node = soup.find(class_="arithmatex")
        
        if node:
            parent_li = node.find_parent("li")
            print(f"[{name}] Found Arithmatex. Inside LI? {parent_li is not None}")
        else:
            print(f"[{name}] No Arithmatex detected.")

if __name__ == "__main__":
    test_list_detection()
