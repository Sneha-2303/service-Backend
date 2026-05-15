import urllib.request
import json

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/reviews") as response:
        status = response.getcode()
        body = response.read().decode('utf-8')
        print(f"Status Code: {status}")
        print(f"Response: {json.loads(body)}")
except Exception as e:
    print(f"Error: {e}")
