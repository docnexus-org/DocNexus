
import unittest
import markdown
from docnexus.core.renderer import render_baseline

class TestMarkdownFeatures(unittest.TestCase):
    """
    Comprehensive test suite for DocNexus Markdown rendering features.
    Verifies support for Math, Definition Lists, CriticMarkup, WikiLinks, and more.
    """

    def test_math_rendering(self):
        """Verify LaTeX math is rendered for KaTeX consumption."""
        text = r"$E=mc^2$"
        html, _ = render_baseline(text)
        # Should render strictly as \( ... \) or \[ ... \] spans for KaTeX
        # OR as <span class="arithmatex">\(...\)</span> depending on output
        # Key check: NOT <script type="math/tex"> (MathJax default)
        self.assertIn(r"\(E=mc^2\)", html)
        self.assertNotIn("script type=\"math/tex\"", html)

    def test_math_block_rendering(self):
        """Verify Block Math $$ syntax."""
        text = """
$$
x = y^2
$$
"""
        html, _ = render_baseline(text)
        self.assertIn(r"\[", html)
        self.assertIn(r"x = y^2", html)
        self.assertIn(r"\]", html)

    def test_definition_lists(self):
        """Verify Definition List syntax."""
        text = """
Term
:   Definition
"""
        html, _ = render_baseline(text)
        self.assertIn("<dl>", html)
        self.assertIn("<dt>Term</dt>", html)
        self.assertIn("<dd>Definition</dd>", html)

    def test_insert_format(self):
        """Verify ++Inserted++ syntax maps to <ins>."""
        text = "++Inserted Text++"
        html, _ = render_baseline(text)
        self.assertIn("<ins>Inserted Text</ins>", html)
    
    def test_mark_format(self):
        """Verify ==Marked== syntax maps to <mark>."""
        text = "==Marked Text=="
        html, _ = render_baseline(text)
        self.assertIn("<mark>Marked Text</mark>", html)

    def test_sub_sup_format(self):
        """Verify Subscript (~) and Superscript (^) syntax."""
        text = "H~2~O and X^2^"
        html, _ = render_baseline(text)
        self.assertIn("H<sub>2</sub>O", html)
        self.assertIn("X<sup>2</sup>", html)

    def test_wikilinks_dots(self):
        """Verify WikiLinks with dots are supported."""
        text = "[[feature_test_v1.2.6]]"
        html, _ = render_baseline(text)
        self.assertIn('href="/file/feature_test_v1.2.6"', html)
        self.assertIn('class="wikilink"', html)

    def test_abbreviations(self):
        """Verify Abbreviation syntax."""
        text = """
The HTML spec.

*[HTML]: Hyper Text Markup Language
"""
        html, _ = render_baseline(text)
        # Check for abbr tag and title attribute
        self.assertIn('<abbr title="Hyper Text Markup Language">HTML</abbr>', html)

if __name__ == '__main__':
    unittest.main()
