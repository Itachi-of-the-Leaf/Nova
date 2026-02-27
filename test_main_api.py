import requests
import json
import time

payload = {
    "references": [
        "Benson, P. (2001). Teaching and researching autonomy in language learning. Harlow: Pearson Education.",
        "Short"
    ]
}

print("Mocking payload to the UI verification endpoint...")
try:
    res = requests.post("http://localhost:8000/verify-crossref", json=payload)
    print("UI RESPONSE STATUS:", res.status_code)
    print("UI RESPONSE PREVIEW:", json.dumps(res.json(), indent=2)[:500])
except Exception as e:
    print("Failed to reach API or UI:", e)
