import pytest
import re
from bs4 import BeautifulSoup, Tag
# Ensure path is set or rely on PYTHONPATH
from docnexus.plugins.pdf_export.plugin import transform_html_for_pdf

class TestPDFFidelity:
    def test_math_transformation(self):
        """
        Verifies KaTeX -> Clean TeX code
        """
        input_html = """
        <div id="documentContent">
            <span class="katex">
                <span class="katex-mathml">
                    <math><semantics>
                        <annotation encoding="application/x-tex">E = mc^2</annotation>
                    </semantics></math>
                </span>
                <span class="katex-html">GARBAGE</span>
            </span>
        </div>
        """
        soup = BeautifulSoup(input_html, 'html.parser')
        transform_html_for_pdf(soup)
        
        assert "E = mc^2" in str(soup)
        assert "GARBAGE" not in str(soup)
        assert "$" in str(soup)

    def test_details_transformation(self):
        """
        Verifies Details -> Styled Div
        """
        input_html = """
        <div id="documentContent">
            <details>
                <summary>Click Me</summary>
                <p>Hidden Content</p>
            </details>
        </div>
        """
        soup = BeautifulSoup(input_html, 'html.parser')
        transform_html_for_pdf(soup)
        
        assert not soup.find('details')
        assert "► Click Me" in str(soup)
        assert "Hidden Content" in str(soup)

    def test_emoji_rendering(self):
        """
        Verifies Emojis are wrapped in span.emoji
        """
        input_html = """
        <div id="documentContent">
            <p>Rocket 🚀 and Sparkles ✨</p>
        </div>
        """
        soup = BeautifulSoup(input_html, 'html.parser')
        transform_html_for_pdf(soup)
        
        # Should be wrapped
        emoji_spans = soup.find_all('span', class_='emoji')
        assert len(emoji_spans) >= 2
        assert "🚀" in emoji_spans[0].text or "🚀" in emoji_spans[1].text

    def test_wikilink_conversion(self):
        """
        Verifies WikiLinks are converted to internal anchors
        """
        input_html = """
        <div id="documentContent">
            <a href="feature_test.md">Link 1</a>
            <a href="section-name">Link 2</a>
            <a href="https://google.com">External</a>
        </div>
        """
        soup = BeautifulSoup(input_html, 'html.parser')
        transform_html_for_pdf(soup)
        
        link1 = soup.find('a', text='Link 1')
        assert link1['href'] == '#feature_test'
        
        link2 = soup.find('a', text='Link 2')
        assert link2['href'] == '#section-name'
        
        ext = soup.find('a', text='External')
        assert ext['href'] == 'https://google.com'

    def test_alert_icon_injection(self):
        """
        Verifies that markdown-alert-title gets an emoji prepended
        AND that the structure is converted to a table for robust rendering.
        """
        input_html = """
        <div class="markdown-alert markdown-alert-note">
            <p class="markdown-alert-title">Note</p>
            <p>Content</p>
        </div>
        """
        soup = BeautifulSoup(input_html, 'html.parser')
        transform_html_for_pdf(soup)
        
        # Verify Table Transformation
        table = soup.find('table')
        assert table is not None
        assert "alert-table" in table.get('class')
        assert "markdown-alert-note" in table.get('class')
        
        # Verify Flattened Content in TD
        td = table.find('td')
        assert "alert-cell" in td.get('class')
        
        # Verify Flattened Title (Bold + Icon Span)
        b_tag = td.find('b')
        assert b_tag is not None
        icon_span = b_tag.find('span', class_='emoji')
        assert icon_span is not None
        assert "ℹ️" in icon_span.get_text()
        assert "Note" in b_tag.get_text()
        
        # Verify Content (should be in text nodes or br, not p depending on implementation)
        # Our implementation extracts content from p.
        assert "Content" in td.get_text()
        # Verify NO p tags inside td
        assert td.find('p') is None

if __name__ == "__main__":
    # Manually run if executed as script
    t = TestPDFFidelity()
    t.test_math_transformation()
    t.test_details_transformation()
    t.test_emoji_rendering()
    t.test_wikilink_conversion()
    t.test_alert_icon_injection()
    print("PDF Fidelity Test Passed!")

