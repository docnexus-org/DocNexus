
import base64

# The string I put in plugin.py
FOOTNOTE_ICON = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAkklEQVRYhe3WMQqAMAxG4QzOHZ09iXdw9QxCt47iUroEBN8H/wOhL95D0pA0JGlI0pAaYK09t7sD2MfZwQ7gCMwO9gBH4OxgD3AEZgd7gCPwd7AH+ArQCdAtIaH1JBgjQukAtA42tBqQ/lT7PAB3tx15k1y/wAAAAABJRU5ErkJggg=="

header, b64_data = FOOTNOTE_ICON.split(',', 1)
print(f"Header: {header}")
print(f"Length: {len(b64_data)}")
padding = len(b64_data) % 4
print(f"Padding needed: {padding}")

try:
    decoded = base64.b64decode(b64_data)
    print("SUCCESS: Valid Base64")
except Exception as e:
    print(f"FAILURE: {e}")
