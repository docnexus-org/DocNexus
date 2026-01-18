
import sys
import os
from docnexus.core.renderer import render_baseline

def debug_math_html():
    md = r"""
# Math Debug
Inline: $E=mc^2$
Block:
$$
\frac{n!}{k!(n-k)!} = \binom{n}{k}
$$
"""
    print("Derived Markdown:")
    print(md)
    
    html, toc = render_baseline(md)
    print("\n--- Rendered HTML ---")
    print(html)

if __name__ == "__main__":
    debug_math_html()
