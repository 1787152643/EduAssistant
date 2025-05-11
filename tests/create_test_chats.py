# create_test_chats.py
import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
NUM_CHATS = 10

# Login credentials
credentials = {
    "username": "student001",
    "password": "123456"
}

# Start a session
session = requests.Session()

# Login
response = session.post(f"{BASE_URL}/login", data=credentials)
if response.status_code != 200:
    print("Login failed")
    exit(1)

# Create multiple chat sessions
chat_ids = []
for i in range(NUM_CHATS):
    response = session.post(f"{BASE_URL}/ai-assistant/chats", json={})
    if response.status_code == 200:
        chat_id = response.json()["id"]
        chat_ids.append(chat_id)
        print(f"Created chat ID: {chat_id}")
    else:
        print(f"Failed to create chat: {response.text}")

# Save chat IDs to file
with open("test_chat_ids.json", "w") as f:
    json.dump(chat_ids, f)

print(f"Created {len(chat_ids)} chat sessions")