import os
import requests

URL = os.environ.get("BACKEND_URL", "http://localhost:8000/chat")


def send_message(message):
    try:
        response = requests.post(URL, json={"message": message})
        return response.json()["answer"]
    except requests.RequestException as e:
        print(f"Error sending message: {e}")
        return "Sorry, I encountered an error while processing your request."
