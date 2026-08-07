import requests

URL = "http://127.0.0.1:8000/chat"


def send_message(message):
    response = requests.post(URL, json={"message": message})

    return response.json()["answer"]
