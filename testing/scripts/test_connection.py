import requests

response = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"message": "Lai suat tiet kiem hien tai la bao nhieu?"},
    timeout=30
)
print("Status code:", response.status_code)
print("Response:", response.json())