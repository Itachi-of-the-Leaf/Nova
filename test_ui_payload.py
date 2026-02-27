import requests

with open("assets/Sample_X_Input_output.json") as f:
    import json
    data = json.load(f)
    refs = data["references"]

print("Mocking payload to the UI verification endpoint...")
try:
    res = requests.post("http://localhost:8000/verify-crossref", json={"text": refs})
    print("UI RESPONSE STATUS:", res.status_code)
    print("UI RESPONSE PREVIEW:", str(res.json())[:300])
except Exception as e:
    print("Failed to reach API or UI:", e)
