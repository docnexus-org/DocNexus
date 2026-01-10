import urllib.request
import requests
import json
import sys
from tests.config import BASE_URL

URL = f"{BASE_URL}/api/plugins"
VERSION_URL = f"{BASE_URL}/api/version"

def test_api():
    print(f"Testing {URL}...")
    try:
        with urllib.request.urlopen(URL) as response:
            if response.status != 200:
                print(f"FAILURE: Status {response.status}")
                sys.exit(1)
            
            data = json.loads(response.read().decode())
            print(f"Plugins found: {len(data)}")
            
            # Verify structure
            found_word_export = False
            found_pdf_export = False
            for p in data:
                print(f" - {p['id']} (type={p['type']}, installed={p.get('installed')})")
                if p['id'] == 'word_export' and p['type'] == 'bundled':
                    found_word_export = True
                if p['id'] == 'pdf_export':
                    found_pdf_export = True
                    # Check initial state (should be False if no ENABLED file, OR True if I created it manually or logical default)
                    # based on my code: default is True for most, but plugin.py overrides it.
            
            if found_word_export:
                print("SUCCESS: word_export found.")
            if found_pdf_export:
                print("SUCCESS: pdf_export found.")
            else:
                 print("FAILURE: pdf_export NOT found.")
            
            if not found_word_export:
                print("FAILURE: word_export not found or not bundled.")
                sys.exit(1)

        print(f"\nTesting {VERSION_URL}...")
        with urllib.request.urlopen(VERSION_URL) as response:
            data = json.loads(response.read().decode())
            print(f"Version: {data['version']}")
            if data['version'] == '1.2.4':
                 print("SUCCESS: Version matches 1.2.4")
            else:
                 print(f"FAILURE: Version mismatch: {data['version']}")
                 sys.exit(1)

    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_api()
