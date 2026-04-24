import os
import json
import requests
import hashlib
import random
from dotenv import load_dotenv
from datetime import datetime
from monikers import NATO_WORDS

load_dotenv()

INTERCOM_TOKEN = os.getenv("INTERCOM_ACCESS_TOKEN")
INTERCOM_ADMIN_ID = os.getenv("INTERCOM_ADMIN_ID")

missing_vars = []
if not INTERCOM_TOKEN:
    missing_vars.append("INTERCOM_ACCESS_TOKEN")
if not INTERCOM_ADMIN_ID:
    missing_vars.append("INTERCOM_ADMIN_ID")

if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

assert INTERCOM_TOKEN is not None
assert INTERCOM_ADMIN_ID is not None

BASE_URL = "https://api.intercom.io"
HEADERS = {
    "Authorization": f"Bearer {INTERCOM_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Intercom-Version": "2.11"
}

# In-memory cache to bridge the gap between creating a conversation and
# Intercom's search index catching up (typically a few seconds).
# Maps contact_id -> conversation_id for recently created conversations.
_recent_conversations: dict[str, str] = {}


def create_or_update_conversation(from_uuid):
    """Creates or updates an Intercom conversation based on a Signal message.
    Only a generic notification is stored -- never the actual message content."""

    print(f"🔎 Searching for contact with UUID: {from_uuid}")
    contact_id = find_or_create_contact(from_uuid)

    # 1) Check Intercom's search index for an open conversation
    conversation_id = _search_open_conversation(contact_id)

    # 2) If search missed, check our local cache (handles index lag)
    if not conversation_id and contact_id in _recent_conversations:
        cached_id = _recent_conversations[contact_id]
        print(f"💾 Search index empty, checking cached conversation #{cached_id}")
        if _verify_conversation_is_open(cached_id):
            conversation_id = cached_id
            print(f"✅ Cached conversation #{cached_id} is still open")
        else:
            del _recent_conversations[contact_id]
            print(f"🗑️ Cached conversation #{cached_id} is no longer open, discarding")

    # 3) Either update or create
    if conversation_id:
        _add_note_to_conversation(conversation_id, contact_id)
    else:
        print("📬 No open conversation found. Creating new one...")
        return create_new_conversation(contact_id)


def _search_open_conversation(contact_id):
    """Searches Intercom's index for an open conversation from this contact."""
    print(f"🔍 Looking for open conversation from contact {contact_id}")
    search_url = f"{BASE_URL}/conversations/search"
    payload = {
        "query": {
            "operator": "AND",
            "value": [
                {"field": "contact_ids", "operator": "=", "value": contact_id},
                {"field": "open", "operator": "=", "value": True}
            ]
        },
        "sort": {
            "field": "updated_at",
            "order": "ascending"
        }
    }

    res = requests.post(search_url, json=payload, headers=HEADERS)
    data = res.json()
    conversations = data.get("conversations", [])

    if conversations:
        conv_id = conversations[0]["id"]
        print(f"🔎 Open conversation found via search: #{conv_id}")
        # Sync cache with reality
        _recent_conversations[contact_id] = conv_id
        return conv_id

    return None


def _verify_conversation_is_open(conversation_id):
    """Directly fetches a conversation by ID to confirm it's still open."""
    res = requests.get(f"{BASE_URL}/conversations/{conversation_id}", headers=HEADERS)
    if res.status_code != 200:
        return False
    data = res.json()
    return data.get("state") == "open"


def _add_note_to_conversation(conversation_id, contact_id):
    """Adds a generic admin note to an existing conversation (no message content)."""
    print(f"✏️ Adding note to existing conversation #{conversation_id} for contact {contact_id}")

    reply_url = f"{BASE_URL}/conversations/{conversation_id}/reply"
    reply_payload = {
        "message_type": "note",
        "type": "admin",
        "admin_id": INTERCOM_ADMIN_ID,
        "body": "New Signal message received"
    }
    response = requests.post(reply_url, json=reply_payload, headers=HEADERS)
    print("📝 Conversation updated:", response.status_code)


def find_or_create_contact(from_uuid):
    """Finds an existing Intercom contact by external_id or creates a new one."""

    hashed_uuid = hash_uuid(from_uuid)
    print(f"🔎 Searching for contact in Intercom: {from_uuid} - {hashed_uuid}")

    search_url = f"{BASE_URL}/contacts/search"
    payload = {
        "query": {
            "field": "external_id",
            "operator": "=",
            "value": hashed_uuid
        }
    }

    res = requests.post(search_url, json=payload, headers=HEADERS)
    data = res.json()

    contacts = data.get("data", [])

    if contacts:
        contact_id = contacts[0]["id"]
        print(f"👤 Found existing contact: {contact_id}")
        return contact_id
    else:
        print("➕ No contact found. Creating new contact...")
        random_moniker = random.choice(NATO_WORDS)
        create_url = f"{BASE_URL}/contacts"
        create_payload = {
            "role": "user",
            "external_id": hashed_uuid,
            "name": f"Signal User ({random_moniker})"
        }
        create_res = requests.post(create_url, json=create_payload, headers=HEADERS)
        contact_data = create_res.json()
        contact_id = contact_data["id"]
        print(f"✅ Contact created with ID: {contact_id}")
        return contact_id


def hash_uuid(uuid: str) -> str:
    return hashlib.sha256(uuid.encode()).hexdigest()


def create_new_conversation(contact_id):
    """Creates a new conversation initiated by the contact (no message content)."""

    url = f"{BASE_URL}/conversations"

    payload = {
        "from": {
            "type": "user",
            "id": contact_id
        },
        "body": "New Signal conversation started"
    }

    response = requests.post(url, json=payload, headers=HEADERS)
    data = response.json()
    print("🎫 New conversation created:")
    print(json.dumps(data, indent=2))

    conversation_id = data.get("conversation_id")

    if conversation_id:
        # Cache immediately so follow-up messages within the index lag window
        # still get routed to this conversation instead of creating duplicates.
        _recent_conversations[contact_id] = conversation_id
        print(f"💾 Cached conversation #{conversation_id} for contact {contact_id}")
        tag_conversation(conversation_id, "signal")

    return conversation_id


def tag_conversation(conversation_id, tag_name):
    """Tags a conversation (e.g. with 'signal'). Creates the tag if it doesn't exist."""
    tag_id = get_or_create_tag(tag_name)
    if not tag_id:
        print(f"⚠️ Could not resolve tag '{tag_name}', skipping")
        return

    url = f"{BASE_URL}/conversations/{conversation_id}/tags"
    payload = {
        "id": tag_id,
        "admin_id": INTERCOM_ADMIN_ID
    }
    res = requests.post(url, json=payload, headers=HEADERS)
    if res.status_code == 200:
        print(f"🏷️ Conversation tagged with '{tag_name}'")
    else:
        print(f"⚠️ Failed to tag conversation: {res.status_code} {res.text}")


def get_or_create_tag(tag_name):
    """Returns the ID of an existing tag, or creates it and returns the new ID."""
    res = requests.post(f"{BASE_URL}/tags", json={"name": tag_name}, headers=HEADERS)
    if res.status_code == 200:
        return res.json().get("id")
    return None
