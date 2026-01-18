
import sys
import os
import io
import re
import markdown
from bs4 import BeautifulSoup

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import plugin logic
from docnexus.plugins.word_export.plugin import transform_html_for_word
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PipelineTest")

def test_pipeline():
    print("==================================================")
    print("TEST: Automated Word Export Pipeline")
    print("==================================================")
    
    # 1. Read Valid Source MD
    md_path = os.path.join(project_root, 'docs', 'examples', 'feature_test_v1.2.6.md')
    if not os.path.exists(md_path):
        logger.error(f"Source file not found: {md_path}")
        sys.exit(1)
        
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
        
    logger.info(f"Read {len(md_content)} bytes form Markdown.")
    
    # 2. Render to HTML (Simulating App)
    # Enabling extensions to match typical Arithmatex output
    html_content = markdown.markdown(
        md_content, 
        extensions=[
            'toc', 'tables', 'fenced_code', 'attr_list', 'def_list', 'abbr',
            'pymdownx.arithmatex', # Math
            'pymdownx.details', 
            'pymdownx.tabbed',
            'pymdownx.emoji',
            'pymdownx.tasklist'
        ],
        extension_configs={
            'pymdownx.arithmatex': {'generic': True} # This generates the raw script tags usually
        }
    )
    
    # Wrap in container to match app structure
    full_html = f'<div class="markdown-content" id="documentContent">{html_content}</div>'
    
    logger.info(f"Generated {len(full_html)} bytes of HTML.")
    
    # 3. Transform
    soup = BeautifulSoup(full_html, 'html.parser')
    
    # DEBUG: Dump initial math HTML
    math_sample = soup.find('script', type=re.compile(r'math/tex'))
    if math_sample:
        logger.info(f"Initial Math Sample: {math_sample.parent.prettify()}")
    else:
        logger.warning("No Math Scripts found in generated HTML! Markdown extension might be misconfigured.")
        
    transform_html_for_word(soup)
    output_html = str(soup)
    
    # 4. Validations
    errors = []
    
    # Math
    if "<img" not in output_html or "latex.codecogs.com" not in output_html:
        # Check if we even had math
        if "E=mc" in output_html:
             errors.append("Math: Formulas present but NOT converted to Images.")
    
    # Check for Garbage Text
    # "n!k!(n-k)!" is the text content of the accessible MathML if not hidden/removed.
    visible_text = soup.get_text()
    if "n!k!" in visible_text and "binom" in visible_text:
        errors.append("Math: Garbage text detected (MathML content visible).")
        
    # Emojis
    if "[:rocket:]" in output_html or "[rocket]" in output_html:
         errors.append("Emoji: Brackets detected.")
         
    # Tabs
    if "<input" in output_html and 'name="__tabbed_' in output_html:
         errors.append("Tabs: Raw input tags detected.")

    if errors:
        print("\n[FAIL] Pipeline Errors:")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Pipeline Validated. Logic works on real file.")

if __name__ == "__main__":
    test_pipeline()
