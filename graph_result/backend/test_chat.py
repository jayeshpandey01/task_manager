import requests
import json

try:
    res = requests.post("http://localhost:8000/api/chat", json={"query": "How many products are there?"})
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Failed to reach server:", e)
