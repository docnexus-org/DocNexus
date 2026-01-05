import urllib.request
import urllib.error
import json
import sys
from pathlib import Path
import argparse

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.config import BASE_URL
URL = f"{BASE_URL}/api/export/docx"
HTML_CONTENT = """
<div id="documentContent">
    <div class="toc-container">
        <div class="toc-header">Table of Contents</div>
        <div class="toc-content">
            <ul>
                <li><a href="#verified-edits">Verified Edits</a></li>
                <li><a href="#docnexus">DocNexus</a></li>
                <li><a href="#future-roadmap">Future Roadmap</a></li>
            </ul>
        </div>
    </div>

    <div class="markdown-content">
        <h1 id="verified-edits"><del>Verified Edits</del></h1>
        <h1 id="docnexus">DocNexus</h1>
        <blockquote>
            <p><strong>The Ultimate All-in-One Document Engine.</strong><br><em>Authority. Universality. Power.</em></p>
        </blockquote>
        <p>
            <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
            <img src="https://example.com/test.svg" alt="External SVG">
            <img src="data:image/svg+xml;base64,fake" alt="Data SVG">
        </p>
        <h2 id="future-roadmap">🔮 Future Roadmap</h2>
    </div>
</div>
"""

def run_manual_test():
    try:
        print(f"Sending POST request to {URL}...")
        
        data = json.dumps({"html": HTML_CONTENT}).encode('utf-8')
        req = urllib.request.Request(URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            print(f"Status Code: {response.status}")
            print(f"Headers: {response.headers}")
            
            if response.status == 200:
                content = response.read()
                content_length = len(content)
                print(f"Response Size: {content_length} bytes")
                
                if content_length > 0:
                    import os
                    output_dir = os.path.join(os.path.dirname(__file__), "output")
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, "test_export.docx")
                    
                    with open(output_path, "wb") as f:
                        f.write(content)
                    print(f"SUCCESS: File downloaded as {output_path}")
                    sys.exit(0)
                else:
                    print("FAILURE: Response content is empty")
                    sys.exit(1)
            else:
                print(f"FAILURE: Unexpected status code {response.status}")
                sys.exit(1)

    except urllib.error.HTTPError as e:
        print(f"FAILURE: HTTP Error {e.code}: {e.reason}")
        print(e.read().decode())
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"FAILURE: Connection Error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_manual_test()
