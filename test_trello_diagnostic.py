"""Diagnose Trello card creation issues."""
import os
from dotenv import load_dotenv
from config import TRELLO_API_KEY, TRELLO_API_TOKEN, TRELLO_BOARD_APPOINTMENTS, TRELLO_BOARD_TICKETS

load_dotenv()

print("=" * 80)
print("Trello Card Creation Diagnostic")
print("=" * 80)

# Test 1: Check credentials
print("\n[1] Checking Trello Credentials")
print("-" * 80)
if TRELLO_API_KEY:
    print("[OK] TRELLO_API_KEY configured")
    print(f"     Length: {len(TRELLO_API_KEY)} chars")
else:
    print("[ERROR] TRELLO_API_KEY not configured")

if TRELLO_API_TOKEN:
    print("[OK] TRELLO_API_TOKEN configured")
    print(f"     Length: {len(TRELLO_API_TOKEN)} chars")
else:
    print("[ERROR] TRELLO_API_TOKEN not configured")

# Test 2: Check board IDs
print("\n[2] Checking Board IDs")
print("-" * 80)
if TRELLO_BOARD_APPOINTMENTS:
    print(f"[OK] TRELLO_BOARD_APPOINTMENTS: {TRELLO_BOARD_APPOINTMENTS}")
else:
    print("[ERROR] TRELLO_BOARD_APPOINTMENTS not configured")

if TRELLO_BOARD_TICKETS:
    print(f"[OK] TRELLO_BOARD_TICKETS: {TRELLO_BOARD_TICKETS}")
else:
    print("[ERROR] TRELLO_BOARD_TICKETS not configured")

# Test 3: Test API connectivity
print("\n[3] Testing Trello API Connectivity")
print("-" * 80)
import requests

try:
    # Test basic auth
    test_url = "https://api.trello.com/1/members/me"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_API_TOKEN
    }
    response = requests.get(test_url, params=params)
    print(f"API Status Code: {response.status_code}")

    if response.status_code == 200:
        print("[OK] Successfully authenticated with Trello API")
        user_data = response.json()
        print(f"     User: {user_data.get('fullName', 'Unknown')}")
    elif response.status_code == 401:
        print("[ERROR] Authentication failed (401 Unauthorized)")
        print("     Check API_KEY and API_TOKEN are correct")
    else:
        print(f"[ERROR] Unexpected status code: {response.status_code}")
        print(f"     Response: {response.text[:200]}")
except Exception as e:
    print(f"[ERROR] Connection error: {e}")

# Test 4: Check if boards exist
print("\n[4] Checking Boards Access")
print("-" * 80)

if TRELLO_BOARD_APPOINTMENTS:
    try:
        board_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_APPOINTMENTS}"
        response = requests.get(board_url, params={"key": TRELLO_API_KEY, "token": TRELLO_API_TOKEN})
        if response.status_code == 200:
            board = response.json()
            print(f"[OK] Appointments Board: {board.get('name', 'Unknown')}")
        else:
            print(f"[ERROR] Cannot access Appointments board (status {response.status_code})")
    except Exception as e:
        print(f"[ERROR] Error checking Appointments board: {e}")

if TRELLO_BOARD_TICKETS:
    try:
        board_url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_TICKETS}"
        response = requests.get(board_url, params={"key": TRELLO_API_KEY, "token": TRELLO_API_TOKEN})
        if response.status_code == 200:
            board = response.json()
            print(f"[OK] Tickets Board: {board.get('name', 'Unknown')}")
        else:
            print(f"[ERROR] Cannot access Tickets board (status {response.status_code})")
    except Exception as e:
        print(f"[ERROR] Error checking Tickets board: {e}")

# Test 5: Check lists
print("\n[5] Checking 'In Queue' Lists")
print("-" * 80)

from trello_tools import get_list_id

if TRELLO_BOARD_APPOINTMENTS:
    list_id = get_list_id(TRELLO_BOARD_APPOINTMENTS, "In Queue")
    if list_id:
        print(f"[OK] Appointments 'In Queue' list found: {list_id}")
    else:
        print("[ERROR] 'In Queue' list not found on Appointments board")
        print("       Checking available lists...")
        try:
            url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_APPOINTMENTS}/lists"
            response = requests.get(url, params={"key": TRELLO_API_KEY, "token": TRELLO_API_TOKEN})
            if response.status_code == 200:
                lists = response.json()
                for lst in lists:
                    status = "open" if not lst.get("closed") else "closed"
                    print(f"       - {lst['name']} ({status}): {lst['id']}")
        except Exception as e:
            print(f"       Error listing: {e}")

if TRELLO_BOARD_TICKETS:
    list_id = get_list_id(TRELLO_BOARD_TICKETS, "In Queue")
    if list_id:
        print(f"[OK] Tickets 'In Queue' list found: {list_id}")
    else:
        print("[ERROR] 'In Queue' list not found on Tickets board")
        print("       Checking available lists...")
        try:
            url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_TICKETS}/lists"
            response = requests.get(url, params={"key": TRELLO_API_KEY, "token": TRELLO_API_TOKEN})
            if response.status_code == 200:
                lists = response.json()
                for lst in lists:
                    status = "open" if not lst.get("closed") else "closed"
                    print(f"       - {lst['name']} ({status}): {lst['id']}")
        except Exception as e:
            print(f"       Error listing: {e}")

# Test 6: Try creating a test card
print("\n[6] Testing Card Creation")
print("-" * 80)

from trello_tools import create_appointment_card

success = create_appointment_card(
    patient_name="Test Patient",
    doctor_name="Test Doctor",
    appointment_date="2026-07-30",
    appointment_time="14:00",
    reason="Test appointment",
    patient_email="test@test.com",
    patient_id="TEST001"
)

if success:
    print("[OK] Test appointment card created successfully")
else:
    print("[ERROR] Failed to create test appointment card")

print("\n" + "=" * 80)
print("Diagnostic Complete")
print("=" * 80)
