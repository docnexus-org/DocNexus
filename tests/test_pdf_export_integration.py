
import os
import sys
import unittest
import shutil

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from docnexus.core.renderer import render_baseline
from docnexus.plugins.pdf_export.plugin import export_pdf

class TestPDFExportIntegration(unittest.TestCase):
    
    def test_full_export_pipeline(self):
        """
        Validates the full pipeline:
        Markdown File -> Core Renderer (HTML) -> PDF Plugin (Transformation + Export) -> PDF File
        """
        print("\nRunning PDF Export Integration Test...")
        
        # 1. Locate Input File
        input_file = os.path.join(project_root, "docs", "examples", "feature_test_v1.2.6.md")
        if not os.path.exists(input_file):
            self.skipTest(f"Input file not found: {input_file}")
            
        print(f"Input: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        # 2. Render Markdown to HTML
        # This uses the actual App Renderer, ensuring all extensions (Mermaid, Emoji, TOC) are active.
        print("Rendering Markdown to HTML...")
        try:
            html_body, toc = render_baseline(md_content)
        except Exception as e:
            self.fail(f"HTML Rendering failed: {e}")
            
        self.assertIsNotNone(html_body)
        self.assertTrue(len(html_body) > 0)
        
        # Wrap in container as the App does
        full_html_container = f'<div class="markdown-content" id="documentContent">{html_body}</div>'
        
        # 3. Export to PDF
        print("Exporting to PDF...")
        try:
            pdf_bytes = export_pdf(full_html_container)
        except Exception as e:
            self.fail(f"PDF Export failed: {e}")
            
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(len(pdf_bytes) > 1000, "PDF bytes should be substantial")
        
        # 4. Save Artifact (optional, for manual inspect)
        # Create 'test_output' dir if not exists
        output_dir = os.path.join(project_root, "tests", "test_output")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "integration_full.pdf")
        with open(output_file, "wb") as f:
            f.write(pdf_bytes)
            
        print(f"SUCCESS: PDF saved to {output_file} ({len(pdf_bytes)} bytes)")
        print("Please visually inspect this file for Emojis, TOC, and Layout.")

if __name__ == "__main__":
    unittest.main()
