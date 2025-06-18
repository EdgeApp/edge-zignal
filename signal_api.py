import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables for Zendesk API
SIGNAL_BRIDGE_NUMBER = os.getenv("SIGNAL_BRIDGE_NUMBER")
SIGNAL_API_BASE = "http://localhost:8080/v1"

# Returns a list of unseen messages received from Signal in JSON format
def receive_messages():
    try:
        response = requests.get(f"{SIGNAL_API_BASE}/receive/{SIGNAL_BRIDGE_NUMBER}")
        if response.status_code == 200:
            return response.json()
        else:
            print("Signal receive failed:", response.text)
            return []
    except Exception as e:
        print("Error receiving from Signal:", str(e))
        return []

def send_signal_message(recipient_uuid, message):
    try:
        payload = {
            "message": message,
            "number": SIGNAL_BRIDGE_NUMBER,
            "recipients": [recipient_uuid]
        }
        response = requests.post(f"{SIGNAL_API_BASE}/send", json=payload)
        
        # debugging
        data = response.json()
        print(f"Message attempt response: {data} \nStatus Code: {response.status_code}")
        # print(json.dumps(data, indent=2))

        if response.status_code == 201:
            print(f"✅ Message sent to {recipient_uuid}")
        else:
            print(f"❌ Failed to send message to {recipient_uuid}: {response.text}")
    except Exception as e:
        print(f"Error sending message to {recipient_uuid}: {str(e)}")
