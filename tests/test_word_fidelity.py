import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tests.export_test_template import WordFidelityVerifier
from docnexus.plugins.word_export.plugin import export_to_word

def test_word_export_fidelity():
    """
    End-to-End fidelity test for Word Export plugin.
    Verifies that Markdown features (Alerts, Math, CriticMarkup) are rendered correctly in DOCX.
    """
    # Setup Paths
    docs_dir = os.path.join(project_root, "docs", "examples")
    md_file = os.path.join(docs_dir, "feature_test_v1.2.6.md")
    output_dir = os.path.join(project_root, "tests", "output")
    
    # Initialize Verifier
    verifier = WordFidelityVerifier(
        input_md_path=md_file, 
        output_dir=output_dir, 
        export_func=export_to_word
    )
    
    # Run Steps
    print("Step 1: Loading and Rendering...")
    verifier.load_and_render()
    
    print("Step 2: Exporting...")
    verifier.run_export()
    
    print("Step 3: Verifying Fidelity...")
    # This will generate the report and log errors/success
    verifier.inspect_docx()
    
    # Assertions
    # 1. Check Output File Exists and is not empty
    assert verifier.output_file.exists(), f"Output DOCX not found at {verifier.output_file}"
    assert verifier.output_file.stat().st_size > 0, "Output DOCX is empty"
    
    # 2. Check Report Content for expected Pass signals
    report_path = verifier.report_path
    assert report_path.exists(), "Fidelity Report not generated"
    
    with open(report_path, "r", encoding="utf-8") as f:
        report_content = f.read()
    
    # Assert Critical Success Criteria found in report
    assert "Total Correctly Colored Alert Tables: 5" in report_content, "Alert Colors check failed"
    assert "Font: Segoe UI Emoji" in report_content, "Icon Font check failed"
    assert "Color=008000" in report_content, "CriticMarkup Insert Color check failed"
    assert "Strike=True" in report_content, "CriticMarkup Delete Strike check failed"
    assert "Fill=f0f0f0" in report_content, "Math Block Shading check failed"
    assert "FAIL: Abbreviation Expanded" not in report_content, "Abbreviation check failed"
    
    # New Round 2 Checks
    assert "PASS: Details transformed to visual block." in report_content, "Details Transformation failed"
    assert "PASS: General Emoji found." in report_content, "General Emoji check failed"
    
    print(f"Fidelity Test PASSED. Report: {report_path}")

if __name__ == "__main__":
    try:
        test_word_export_fidelity()
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)

