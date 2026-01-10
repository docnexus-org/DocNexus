import urllib.request
import urllib.error
import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.config import BASE_URL
URL = f"{BASE_URL}/api/export/pdf"
HTML_CONTENT = "<div>Test</div>"

def verify_pdf_block():
    print(f"Testing blocked state on {URL}...")
    try:
        data = json.dumps({"html": HTML_CONTENT}).encode('utf-8')
        req = urllib.request.Request(URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            # If we get here, it SUCCEEDED (200 OK), which is bad if we expect it to be blocked
            print(f"FAILURE: Request succeeded with {response.status}. It should have been blocked.")
            sys.exit(1)
            
    except urllib.error.HTTPError as e:
        print(f"Received HTTP {e.code}")
        body = e.read().decode()
        print(f"Body: {body}")
        
        if e.code == 404:
            try:
                resp = json.loads(body)
                if resp.get('code') == 'MISSING_PLUGIN':
                    print("SUCCESS: PDF Export correctly blocked with MISSING_PLUGIN code.")
                    sys.exit(0)
                else:
                    print(f"FAILURE: Got 404 but unexpected body: {resp}")
                    sys.exit(1)
            except json.JSONDecodeError:
                print("FAILURE: Got 404 but body was not JSON")
                sys.exit(1)
        else:
             print(f"FAILURE: Unexpected HTTP error code {e.code}")
             sys.exit(1)
             
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_pdf_block()
