import urllib.request
import json
import sys

URL = "http://localhost:8000/api/plugins"
VERSION_URL = "http://localhost:8000/api/version"

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
            for p in data:
                print(f" - {p['id']} ({p['type']})")
                if p['id'] == 'word_export' and p['type'] == 'bundled':
                    found_word_export = True
            
            if found_word_export:
                print("SUCCESS: word_export found as bundled.")
            else:
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
