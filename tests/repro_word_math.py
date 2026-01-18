import re
import bs4
from bs4 import BeautifulSoup
import logging

# Configure Logging
logging.basicConfig(filename='tests/repro_result.txt', level=logging.INFO, filemode='w', encoding='utf-8')
logger = logging.getLogger("ReproMath")

# Console handler for sanity
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

def repro_logic(html_snippet, description):
    logger.info(f"--- Testing {description} ---")
    soup = BeautifulSoup(html_snippet, 'html.parser')
    
    # --- LOGIC START (Copied from plugin.py) ---
    import re
    import urllib.parse
    
    # --- PRE-CLEANUP: Remove MathJax Previews ---
    for junk in soup.find_all(class_=['MathJax_Preview', 'katex-html', 'katex-mathml']):
        if junk.parent:
            junk.decompose()
            
    # Collect candidates
    math_candidates = []
    
    math_candidates.extend(soup.find_all('script', type=re.compile(r'math/tex')))
    math_candidates.extend(soup.find_all(class_='arithmatex'))
    math_candidates.extend(soup.find_all(class_='katex'))
    
    processed_math_ids = set()
    
    logger.info(f"Found {len(math_candidates)} initial math candidates.")
    
    logger.info(f"Found {len(math_candidates)} initial math candidates.")
    
    for i, node in enumerate(math_candidates):
        if id(node) in processed_math_ids:
            continue
            
        target_node = node
        parent = node.parent
        
        # Debug: Log the initial node structure
        try:
            node_class = node.get('class') if hasattr(node, 'get') else 'N/A'
            logger.info(f"Analyzing Candidate {i}: Tag={node.name}, Classes={node_class}")
        except Exception as e:
            logger.error(f"Error logging candidate {i}: {e}")
            continue

        # Handle wrappings
        try:
            # If node is a script inside arithmatex/MathJax div, target the DIV
            if node.name == 'script' and parent and hasattr(parent, 'get') and ('arithmatex' in (parent.get('class') or []) or 'MathJax' in str(parent.get('class') or [])):
                target_node = parent
                logger.info(f"Escalated target to parent (Script -> Wrapper): {target_node.name} {target_node.get('class')}")
            
            # If node is .katex inside .arithmatex, target .arithmatex
            if target_node.name == 'span' and hasattr(target_node, 'get') and 'katex' in (target_node.get('class') or []) and parent and hasattr(parent, 'get') and ('arithmatex' in (parent.get('class') or [])):
                target_node = parent
                logger.info(f"Escalated target to parent (.katex -> .arithmatex): {target_node.name} {target_node.get('class')}")
        except Exception as e:
             logger.error(f"Error handling wrappings for candidate {i}: {e}")
             continue

        if id(target_node) in processed_math_ids:
            continue
            
        tex = ""
        is_display = False
        
        # Extraction Strategy
        script_child = target_node if target_node.name == 'script' else target_node.find('script', type=re.compile(r'math/tex'))
        # Loosen search to any annotation, prioritizing tex
        annotation_child = target_node.find('annotation', attrs={'encoding': 'application/x-tex'})
        if not annotation_child:
            annotation_child = target_node.find('annotation')
        
        if script_child:
            tex = script_child.get_text()
            is_display = 'mode=display' in script_child.get('type', '')
            processed_math_ids.add(id(script_child))
            logger.info("Extracted TeX from Script.")
            
        elif annotation_child:
            tex = annotation_child.get_text().strip()
            is_display = (target_node.name == 'div') or \
                         ('display' in (target_node.get('class') or [])) or \
                         ('katex-display' in target_node.decode_contents()) or \
                         (target_node.find_parent(class_='katex-display') is not None)
            logger.info("Extracted TeX from Annotation.")
        
        if not tex or not tex.strip():
            logger.warning(f"Failed to extract TeX from candidate {target_node.name}. Decomposing.")
            target_node.decompose()
            processed_math_ids.add(id(target_node))
            continue
            
        # Clean Tex
        tex = tex.strip()
        logger.info(f"Generated TeX: {tex}")
        
        # Construct CodeCogs URL
        base_url = "https://latex.codecogs.com/png.image"
        params = f"\\dpi{{300}} {tex}"
        safe_params = urllib.parse.quote(params)
        img_url = f"{base_url}?{safe_params}"
        
        # Create IMG tag
        img_tag = soup.new_tag('img')
        img_tag['src'] = img_url
        img_tag['alt'] = tex
        
        replacement = img_tag
        if is_display:
            div = soup.new_tag('div')
            div.append(img_tag)
            replacement = div
            
        target_node.replace_with(replacement)
        processed_math_ids.add(id(target_node))
        
    # Final Cleanup Pass
    for junk in soup.find_all(class_=['MathJax_Preview', 'katex-html', 'katex-mathml']):
        if junk.parent:
            junk.decompose()
            
    # --- RESULT ---
    logger.info(f"Result HTML: {soup.prettify()}")

# Test Case 1: Legacy MathJax Script
html_1 = """
<div class="arithmatex">
  <script type="math/tex; mode=display">E = mc^2</script>
  <span class="MathJax_Preview">E = mc2</span>
</div>
"""

# Test Case 2: Modern Arithmatex / KaTeX
html_2 = """
<div class="arithmatex">
  <span class="katex">
    <span class="katex-mathml">
      <math xmlns="http://www.w3.org/1998/Math/MathML">
        <semantics>
          <mrow><mi>E</mi><mo>=</mo><mi>m</mi><msup><mi>c</mi><mn>2</mn></msup></mrow>
          <annotation encoding="application/x-tex">E = mc^2</annotation>
        </semantics>
      </math>
    </span>
    <span class="katex-html" aria-hidden="true">
        <span class="base">Garbage Visual Text</span>
    </span>
  </span>
</div>
"""

# Test Case 3: Mixed Garbage (Simulating User Issue)
html_3 = """
<div class="arithmatex">
    E=mc2
    <span class="katex-mathml">E=mc^2</span>
    <script type="math/tex">E=mc^2</script>
</div>
"""

# Test Case 4: Missing TeX (Should Decompose)
html_4 = """
<div class="arithmatex">
    <span class="katex-html">Garbage</span>
</div>
"""

if __name__ == "__main__":
    repro_logic(html_1, "Case 1: MathJax Script")
    repro_logic(html_2, "Case 2: KaTeX Structure")
    repro_logic(html_3, "Case 3: Mixed Garbage")
    repro_logic(html_4, "Case 4: Broken/Missing TeX")
