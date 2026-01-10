import urllib.request
import urllib.error
import json
import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.config import BASE_URL
EXPORT_URL = f"{BASE_URL}/api/export/pdf"
INSTALL_URL = f"{BASE_URL}/api/plugins/install/pdf_export"
UNINSTALL_URL = f"{BASE_URL}/api/plugins/uninstall/pdf_export"
HTML_CONTENT = "<div>Test Uninstall Hot Reload</div>"

def verify_uninstall_hot_reload():
    print("--- STEP 0: Ensure Installed ---")
    try:
        urllib.request.urlopen(urllib.request.Request(INSTALL_URL, method='POST'))
        print("Installed PDF plugin.")
    except Exception as e:
        print(f"Install failed (maybe already installed): {e}")

    print("\n--- STEP 1: Verify It Works ---")
    try:
        data = json.dumps({"html": HTML_CONTENT}).encode('utf-8')
        req = urllib.request.Request(EXPORT_URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as r:
            if r.status == 200:
                print("SUCCESS: PDF Export is working.")
            else:
                 print(f"FAILURE: PDF Export failed with {r.status}")
                 sys.exit(1)
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)

    print("\n--- STEP 2: Uninstall (Hot Reload) ---")
    try:
        req = urllib.request.Request(UNINSTALL_URL, method='POST')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("SUCCESS: Uninstall triggered.")
            else:
                print(f"FAILURE: Uninstall failed with {response.status}")
                sys.exit(1)
    except Exception as e:
        print(f"FAILURE: Uninstall call crashed: {e}")
        sys.exit(1)

    print("\n--- STEP 3: Verify It IS BLOCKED ---")
    try:
        data = json.dumps({"html": HTML_CONTENT}).encode('utf-8')
        req = urllib.request.Request(EXPORT_URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
             print(f"FAILURE: Request succeeded with {response.status}. It should have been blocked (404)!")
             sys.exit(1) # Fail if it works
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("SUCCESS: Uninstall Hot Reload worked! PDF Export is correctly blocked.")
            sys.exit(0)
        else:
            print(f"FAILURE: Unexpected code {e.code}")
            sys.exit(1)
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_uninstall_hot_reload()
