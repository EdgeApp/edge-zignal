import os
import json
import requests
import hashlib
import random
from dotenv import load_dotenv
from monikers import GREEK_ALPHABET, PLANETS, COLORS, FAMOUS_SCIENTISTS, ANIMALS, US_STATES, STAR_CONSTELLATIONS, MYTHOLOGICAL_FIGURES, TREE_SPECIES, FRUITS

# Load environment variables from .env file
load_dotenv()

# Load environment variables for Zendesk API
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
ZENDESK_TOKEN = os.getenv("ZENDESK_API_TOKEN")
ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
ZENDESK_USER = os.getenv("ZENDESK_USER")
ZENDESK_SIGNAL_UUID_FIELD_RAW = os.getenv("ZENDESK_SIGNAL_UUID_FIELD")
ZENDESK_SIGNAL_UUID_FIELD = None  # type: int | None

# Check for required environment variables
missing_vars = []
if not ZENDESK_EMAIL:
    missing_vars.append("ZENDESK_EMAIL")
if not ZENDESK_TOKEN:
    missing_vars.append("ZENDESK_API_TOKEN")
if not ZENDESK_SUBDOMAIN:
    missing_vars.append("ZENDESK_SUBDOMAIN")
if not ZENDESK_USER:
    missing_vars.append("ZENDESK_USER")
if not ZENDESK_SIGNAL_UUID_FIELD_RAW:
    missing_vars.append("ZENDESK_SIGNAL_UUID_FIELD")

if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

ZENDESK_SIGNAL_UUID_FIELD = int(ZENDESK_SIGNAL_UUID_FIELD_RAW)  # type: ignore

AUTH = (f"{ZENDESK_EMAIL}/token", ZENDESK_TOKEN)
HEADERS = { "Content-Type": "application/json" }

# Random naming convention
NATO_WORDS = [
    "Alfa", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot",
    "Golf", "Hotel", "India", "Juliett", "Kilo", "Lima",
    "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo",
    "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "X-ray",
    "Yankee", "Zulu"
]

# Creates or updates a Zendesk ticket based on a Signal message
def create_or_update_ticket(from_uuid, message):
    
    print(f"🔎 Searching for user with UUID: {from_uuid}")
    user_id = find_or_create_user(from_uuid)

    search_url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/search.json"
    
    # Default sorting
    params = {
        "sort_by": 'updated_at',
        "sort_order": 'asc'
    }

    tag = "signal"

    # Search for unsolved tickets from this user
    query = f'requester_id:{user_id} -status:solved -status:closed'
    
    params["query"] = query

    print(f"🔍 Looking for unsolved ticket from user Zendesk {user_id}")
    # Search zendesk for existing ticket
    res = requests.get(search_url, params=params, auth=AUTH, headers=HEADERS)
    data = res.json()

    if data.get("count", 0) > 0:
        print("🔎 Zendesk Ticket Found:")
        # print(json.dumps(data, indent=2))
        # smallerData = data
        # smallerData["results"][0]["custom_fields"] = []
        # smallerData["results"][0]["fields"] = []

        print(json.dumps(data, indent=2))

    ####################################################
    # Step 3: Update existing ticket or create a new one
    # check if count is greater than 0 or if the results are empty array (aka ticket was deleted but Zendesk api still returns empty results because of caching)
    if data.get("count", 0) > 0 and data["results"]:
        # Update the first ticket found
        ticket_id = data["results"][0]["id"]
        print(f"✏️ Updating existing ticket #{ticket_id} for userID {user_id}")

        url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
        payload = {
            "ticket": {
                "comment": {
                    "body": "New Signal message received",
                    "author_id": user_id,
                    "public": False  # Set to False for internal notes
                },
                "status": "open",
                "requester_id": user_id
            }
        }
        response = requests.put(url, json=payload, auth=AUTH, headers=HEADERS)
        print("📝 Ticket updated:", response.status_code)
        # don't return if ticket is only updated because returned ID means new ticket
        # return ticket_id
    else:
        # No ticket found — create one
        print("📬 No open ticket found. Creating new one...")
        # Return ticket number to be shared with user in auto response
        return create_new_ticket(user_id, "signal", message)

# Finds an existing Zendesk user by phone number or creates a new one
# 
def find_or_create_user(from_uuid):
    
    # Hash the UUID to use as a unique identifier in Zendesk
    hashed_uuid = hash_uuid(from_uuid)

    print(f"🔎 Searching for user matching user in Zendesk: {from_uuid} - {hashed_uuid}")
    
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users/search.json"
    params = { "external_id": hashed_uuid }

    res = requests.get(url, params=params, auth=AUTH, headers=HEADERS)
    data = res.json()


    # Returns user ID if found, otherwise creates a new user
    if data.get("count", 0) > 0:
        user_id = data["users"][0]["id"]
        print(f"👤 Found existing user: {user_id}")
        return user_id
    else:
        # No user found, create one
        print("➕ No user found. Creating new user...")
        random_word = random.choice(NATO_WORDS) # give user a random name
        create_url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users.json"
        payload = {
            "user": {
                "name": f'Signal User ({random_word})',
                "external_id": hashed_uuid
                
            }
        }
        create_res = requests.post(create_url, json=payload, auth=AUTH, headers=HEADERS)
        user_data = create_res.json()
        user_id = user_data["user"]["id"]
        print(f"✅ User created with ID: {user_id}")
        return user_id

# Return hashed version of Signal UUID
def hash_uuid(uuid: str) -> str:
    return hashlib.sha256(uuid.encode()).hexdigest()

# Creates a new ticket attached to zendesk user id (requester_id)
def create_new_ticket(requester_id, tag, message=None):
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets.json"

    # random_moniker = random.choice(GREEK_ALPHABET)
    # subject = f"Signal Request ({random_moniker})"
    subject = f"Signal Request" 

    payload = {
        "ticket": {
            "subject": subject,
            "comment": {
                "body": "New Signal ticket created",
                # "author_id": user_id,  # Necessary?
                "public": False # Set to False for internal notes
            },
            "tags": [tag],
            "requester_id": requester_id
        }
    }

    response = requests.post(url, json=payload, auth=AUTH, headers=HEADERS)

    # Debugging output
    data = response.json()
    print("🎫 New ticket created:")

    smallerData = data
    smallerData["ticket"]["custom_fields"] = []
    smallerData["ticket"]["fields"] = []
    smallerData["audit"]["events"] = []

    print(json.dumps(smallerData, indent=2))

    return data["ticket"]["id"]
    # print("🎫 New ticket created:", response.status_code, response.text)

