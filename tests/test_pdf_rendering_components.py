
import sys
import os
import io
from bs4 import BeautifulSoup

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import plugin logic
from docnexus.plugins.pdf_export.plugin import transform_html_for_pdf

def test_pdf_rendering_components():
    print("==================================================")
    print("TEST: PDF Rendering Components (Math, Checklist, Footnote)")
    print("==================================================")

    html_input = """
    <div class="markdown-content" id="documentContent">
        <h1>Comprehensive PDF Test</h1>
        
        <!-- 1. Math Test -->
        <h3>Math Formulas</h3>
        <p>Inline: <script type="math/tex">E=mc^2</script></p>
        <p>Block:</p>
        <script type="math/tex; mode=display">
            \\frac{n!}{k!(n-k)!} = \\binom{n}{k}
        </script>

        <!-- 2. Checklist Test -->
        <h3>Task Lists</h3>
        <ul class="task-list">
            <li class="task-list-item">
                <input type="checkbox" class="task-list-item-checkbox" disabled> Incomplete Task
            </li>
            <li class="task-list-item">
                <input type="checkbox" class="task-list-item-checkbox" checked disabled> Completed Task
            </li>
        </ul>

        <!-- 3. Footnote Test -->
        <h3>Footnotes</h3>
        <p>Text with footnote<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup>.</p>
        <div class="footnote">
            <hr />
            <ol>
                <li id="fn:1">
                    <p>Footnote content.<a class="footnote-backref" href="#fnref:1" title="Jump back to footnote 1 in the text">↩</a></p>
                </li>
            </ol>
        </div>

        <!-- 4. Definition List Test -->
        <h3>Definition List</h3>
        <dl>
            <dt>Term 1</dt>
            <dd>Definition 1</dd>
        </dl>
        
        <!-- 5. Abbreviation Test -->
        <h3>Abbreviations</h3>
        <p>The <abbr title="Hyper Text Markup Language">HTML</abbr> specification.</p>

    </div>
    """

    soup = BeautifulSoup(html_input, 'html.parser')
    
    print("\n[INFO] Transforming HTML...")
    transform_html_for_pdf(soup)
    output_html = str(soup)
    
    # --- Validations ---
    print("\n[INFO] Validating Output...")
    errors = []

    # 1. Math
    if "<img" not in output_html or "data:image/png;base64" not in output_html:
        # Note: Math might fail if network is down/blocked, but structure should change.
        # Ideally we check for img or generic span fallback if request fails.
        # But our plugin prints debugs. 
        if "$E=mc^2$" not in output_html and "<img" not in output_html:
             errors.append("Math: Neither Image nor Fallback Text found.")
    else:
        print("[PASS] Math: Image tags generated.")

    # 2. Checklist
    if '<input' in output_html:
         errors.append("Checklist: Raw <input> tag found (Should be replaced).")
    elif '☑' not in output_html and '☐' not in output_html and 'data:image/png;base64' not in output_html:
         # We use images now, so check for images or the alt text?
         # Our code uses alt="[x]" or "[ ]"
         if '[x]' not in output_html and '[ ]' not in output_html:
             errors.append("Checklist: No visual replacement found.")
         else:
             print("[PASS] Checklist: Replaced with Icons.")
    else:
         print("[PASS] Checklist: Replaced with Icons (Images detected).")

    # 3. Footnote
    if '<table class="footnote-table"' not in output_html:
        errors.append("Footnote: Table structure not found.")
    else:
        print("[PASS] Footnote: Converted to Table.")

    # 4. Definition List
    if '<strong>Term 1</strong>' not in output_html and '<b>Term 1</b>' not in output_html:
         # Note: Our code uses factory_soup.new_tag('strong').
         errors.append("Definition List: Term not bolded.")
    else:
        print("[PASS] Definition List: Term bolded.")

    # 5. Abbreviation
    if 'HTML (Hyper Text Markup Language)' not in output_html:
         errors.append("Abbreviation: First-use expansion missing.")
    else:
        print("[PASS] Abbreviation: Expanded correctly.")


    if errors:
        print("\n[FAIL] Errors found:")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All PDF Component tests passed.")

if __name__ == "__main__":
    test_pdf_rendering_components()
