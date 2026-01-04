import urllib.request
import urllib.error
import json
import sys

URL = "http://localhost:8000/api/export/docx"
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
        </p>
        <h2 id="future-roadmap">🔮 Future Roadmap</h2>
    </div>
</div>
"""

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
                with open("test_export.docx", "wb") as f:
                    f.write(content)
                print("SUCCESS: File downloaded as test_export.docx")
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
