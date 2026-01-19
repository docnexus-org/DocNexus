
import os

file_path = r"d:\Code\DocNexusCorp\DocNexus\docnexus\plugins\pdf_export\plugin.py"

content_to_append = r'''
# -------------------------------------------------------------------------
# Integration Test
# -------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import io
    
    print("Running Integrated PDF Export Test...")
    
    test_html = """
    <div class="markdown-content" id="documentContent">
        <h1>Emoji Fidelity Test</h1>
        <p>This is a test of the export_pdf function.</p>
        <p>Emoji: 🚀 (Rocket)</p>
        <p>Emoji: ❤️ (Heart)</p>
        <div class="admonition note">
            <p class="admonition-title">Note</p>
            <p>This is a note with an icon.</p>
        </div>
    </div>
    """
    
    try:
        # Assuming export_pdf is available in the module scope
        # (It is, as this code runs in the module)
        pdf_bytes = export_pdf(test_html)
        
        if pdf_bytes and len(pdf_bytes) > 0:
            output_file = "integration_test.pdf"
            with open(output_file, "wb") as f:
                f.write(pdf_bytes)
            print(f"SUCCESS: Generated {output_file} ({len(pdf_bytes)} bytes)")
            print("Please verify the emojis in this file visually.")
        else:
            print("FAILURE: export_pdf returned empty bytes.")
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
'''

with open(file_path, "a", encoding="utf-8") as f:
    f.write(content_to_append)

print("Successfully appended integration test to plugin.py")
