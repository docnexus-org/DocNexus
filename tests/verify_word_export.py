import urllib.request
import urllib.error
import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.config import BASE_URL
URL = f"{BASE_URL}/api/export/docx"
HTML_CONTENT = "<div>Test Word Export</div>"

def verify_word_export():
    print(f"Testing functionality of Pre-Installed plugin on {URL}...")
    try:
        data = json.dumps({"html": HTML_CONTENT}).encode('utf-8')
        req = urllib.request.Request(URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("SUCCESS: Word Export (Pre-installed) works as expected.")
                sys.exit(0)
            else:
                print(f"FAILURE: Unexpected status block {response.status}")
                sys.exit(1)
            
    except urllib.error.HTTPError as e:
        print(f"FAILURE: Received HTTP {e.code}")
        print(e.read().decode())
        sys.exit(1)
             
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_word_export()
