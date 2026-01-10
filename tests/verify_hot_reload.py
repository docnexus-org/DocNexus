import urllib.request
import urllib.error
import json
import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force cleanup of ENABLED file to start fresh
PLUGIN_DIR = PROJECT_ROOT / "docnexus" / "plugins" / "pdf_export"
ENABLED_FILE = PLUGIN_DIR / "ENABLED"
print(f"DEBUG: Removing ENABLED file at {ENABLED_FILE} if exists...")
if ENABLED_FILE.exists():
    try:
        os.remove(ENABLED_FILE)
        print("Removed ENABLED file.")
    except Exception as e:
        print(f"Failed to remove ENABLED file: {e}")

from tests.config import BASE_URL
EXPORT_URL = f"{BASE_URL}/api/export/pdf"
INSTALL_URL = f"{BASE_URL}/api/plugins/install/pdf_export"
HTML_CONTENT = "<div>Test Hot Reload</div>"

def verify_hot_reload():
    print("--- STEP 1: Verify Initial Block ---")
    try:
        data = json.dumps({"html": HTML_CONTENT}).encode('utf-8')
        req = urllib.request.Request(EXPORT_URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req)
        print("FAILURE: Initial request should have been blocked (404)!")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("SUCCESS: Initially blocked.")
        else:
            print(f"FAILURE: Unexpected code {e.code}")
            sys.exit(1)

    print("\n--- STEP 2: Trigger Install (Hot Reload) ---")
    try:
        req = urllib.request.Request(INSTALL_URL, method='POST')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("SUCCESS: Install triggered.")
            else:
                print(f"FAILURE: Install failed with {response.status}")
                sys.exit(1)
    except Exception as e:
        print(f"FAILURE: Install call crashed: {e}")
        sys.exit(1)

    print("\n--- STEP 3: Verify Unblocked Export ---")
    try:
        data = json.dumps({"html": HTML_CONTENT}).encode('utf-8')
        req = urllib.request.Request(EXPORT_URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
             if response.status == 200:
                 print("SUCCESS: Hot Reload worked! PDF Export is active.")
             else:
                 print(f"FAILURE: Export failed with {response.status} after install.")
                 sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"FAILURE: Still getting {e.code} after install. Hot Reload failed.")
        print(e.read().decode())
        sys.exit(1)
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_hot_reload()
