import urllib.request
import urllib.parse
import json
import time
import sys
from tests.config import BASE_URL

# Endpoints
GET_SOURCE_URL = f"{BASE_URL}/api/get-source"
SAVE_DOC_URL = f"{BASE_URL}/api/save-document"

def test_editor_api():
    print(f"Running Editor API Tests against {BASE_URL}...")
    
    # 1. Test Get Source
    test_file = "examples/Welcome.md"
    url = f"{GET_SOURCE_URL}/{test_file}"
    print(f"\n1. Testing GET {url}")
    
    content = ""
    try:
        try:
             response = urllib.request.urlopen(url)
        except urllib.error.HTTPError:
             # Retry with simple path
             test_file = "Welcome.md"
             url = f"{GET_SOURCE_URL}/{test_file}"
             print(f"   Retrying with {url}")
             response = urllib.request.urlopen(url)

        with response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                content = data.get('content')
                print(f"   SUCCESS: Retrieved source ({len(content)} bytes).")
            else:
                print(f"   FAILURE: Status {response.status}")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"   CRASH: HTTP Error {e.code}: {e.reason}")
        print(f"   Body: {e.read().decode('utf-8')[:200]}")
        sys.exit(1)
    except Exception as e:
        print(f"   CRASH: {e}")

    # 2. Test Save
    print(f"\n2. Testing POST {SAVE_DOC_URL}")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    new_content = content + f"\n\n<!-- Editor Test {timestamp} -->"
    
    payload = json.dumps({
        "filename": test_file,
        "content": new_content
    }).encode('utf-8')
    
    req = urllib.request.Request(
        SAVE_DOC_URL, 
        data=payload, 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
             if response.status == 200:
                 resp_data = json.loads(response.read().decode())
                 backup_path = resp_data.get('backup')
                 print(f"   SUCCESS: Document saved.")
                 print(f"   Backup created at: {backup_path}")
             else:
                 print(f"   FAILURE: Status {response.status}")
                 sys.exit(1)

    except Exception as e:
        print(f"   CRASH: {e}")
        sys.exit(1)

    print("\nEditor API Tests check: PASSED")

if __name__ == "__main__":
    test_editor_api()
