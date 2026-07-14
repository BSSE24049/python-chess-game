import urllib.request
import os

# Test downloading size 60 and size 100 and size 150
sizes = [60, 100, 150]
for size in sizes:
    url = f"https://www.chess.com/chess-themes/pieces/neo/{size}/wp.png"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read()
            print(f"Size {size} downloaded successfully! Bytes: {len(content)}")
    except Exception as e:
        print(f"Size {size} failed: {e}")
