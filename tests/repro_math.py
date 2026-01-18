
import sys
import os
import io
import markdown
from bs4 import BeautifulSoup

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import plugin logic
from docnexus.plugins.pdf_export.plugin import transform_html_for_pdf

def repro_math_rendering():
    # 1. Input Markdown (Simulating feature_test_v1.2.6.md math section)
    md_content = """
# Math Test

### 2.3 Math (Arithmatex)
- Inline: $E=mc^2$
- Block:

$$
\\frac{n!}{k!(n-k)!} = \\binom{n}{k}
$$
"""
    
    # 2. Convert to HTML using same extensions as App
    # Assuming 'pymdownx.arithmatex' is used with generic setup
    html = markdown.markdown(
        md_content,
        extensions=['pymdownx.arithmatex'],
        extension_configs={
            'pymdownx.arithmatex': {
                'generic': True, # Outputs <script type="math/tex"> usually? 
                # actually 'generic': True output: \( ... \) and \[ ... \] ?
                # The existing plugin code looks for <script type="math/tex"> 
                # which implies MathJax legacy format.
                # Let's try standard mathjax config which Arithmatex supports.
            } 
        }
    )
    
    # Wait, if 'generic' is True, arithmatex outputs \(..\).
    # If the user's setup outputs <script>, they might be using older config or 'mathjax' mode?
    # Let's check what the plugin EXPECTS. The plugin expects <script type="math/tex">.
    # So we should try to simulate that output or see what actual MD conversion produces.
    # For now, let's artificially construct the HTML that the plugin sees, 
    # based on the fact that existing plugin code finds these tags.
    
    input_html = """
    <div class="markdown-body">
        <p>Inline: <script type="math/tex">E=mc^2</script></p>
        <p>Block:</p>
        <script type="math/tex; mode=display">
            \\frac{n!}{k!(n-k)!} = \\binom{n}{k}
        </script>
    </div>
    """
    
    print("--- Input HTML ---")
    print(input_html)
    
    soup = BeautifulSoup(input_html, 'html.parser')
    
    # 3. Transform
    transform_html_for_pdf(soup)
    
    # 4. Inspect Output
    print("\n--- Transformed HTML (for PDF) ---")
    output_html = str(soup)
    print(output_html)
    
    # Validation
    if "<img" in output_html:
        print("\n[PASS] Found <img> tag for math.")
    elif "E=mc^2" in output_html and "$" in output_html:
        print("\n[FAIL] Found raw text with $ separators (Current Behavior).")
    else:
        print("\n[?] Unknown output structure.")

if __name__ == "__main__":
    repro_math_rendering()
