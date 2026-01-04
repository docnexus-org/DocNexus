import urllib.request
import urllib.error
import json
import sys

URL = "http://localhost:8000/api/export/docx"
HTML_CONTENT = """
<div class="markdown-content">
    <h1>Verification Document</h1>
    <p>This is a test paragraph to verify the Word export functionality.</p>
    <p>Testing resilience against missing images:</p>
    <img src="non_existent_image.png" alt="Broken Image">
    <p>End.</p>
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
