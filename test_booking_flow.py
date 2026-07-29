"""Debug script to test the booking flow with your test case."""
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

print("=" * 80)
print("Testing Booking Flow Debug")
print("=" * 80)

# Test 1: Date/time parser
print("\n[1] Testing Date/Time Parser")
print("-" * 80)
from date_time_parser import parse_date_time, format_appointment_date_time

user_input = "I need a ophthalmologist tomorrow. I have sight issue. My Patient_ID: P002. Sergii Vakulenko; test@test.com at 12:34 PM"
parsed = parse_date_time(user_input)
print(f"User input: {user_input}")
print(f"Parsed date: {parsed['appointment_date']}")
print(f"Parsed time: {parsed['appointment_time']}")
formatted = format_appointment_date_time(parsed['appointment_date'], parsed['appointment_time'])
print(f"Formatted: {formatted}")

# Test 2: Info extraction
print("\n\n[2] Testing Info Extraction")
print("-" * 80)
from info_extractor import _extract_specialization_from_input
from intent_detector import extract_patient_id

extracted_spec = _extract_specialization_from_input(user_input)
extracted_id = extract_patient_id(user_input)
print(f"Extracted specialization: {extracted_spec}")
print(f"Extracted patient ID: {extracted_id}")

# Test 3: Trello credentials
print("\n\n[3] Checking Trello Credentials")
print("-" * 80)
from config import TRELLO_API_KEY, TRELLO_API_TOKEN, TRELLO_BOARD_APPOINTMENTS, TRELLO_BOARD_TICKETS

has_key = 'YES' if TRELLO_API_KEY else 'NO'
has_token = 'YES' if TRELLO_API_TOKEN else 'NO'
print(f"TRELLO_API_KEY present: {has_key}")
print(f"TRELLO_API_TOKEN present: {has_token}")
print(f"TRELLO_BOARD_APPOINTMENTS: {TRELLO_BOARD_APPOINTMENTS or 'NOT CONFIGURED'}")
print(f"TRELLO_BOARD_TICKETS: {TRELLO_BOARD_TICKETS or 'NOT CONFIGURED'}")

# Test 4: Trello list retrieval
print("\n\n[4] Testing Trello List Retrieval")
print("-" * 80)
if TRELLO_BOARD_APPOINTMENTS and TRELLO_API_KEY and TRELLO_API_TOKEN:
    from trello_tools import get_list_id

    list_id = get_list_id(TRELLO_BOARD_APPOINTMENTS, "In Queue")
    if list_id:
        print(f"SUCCESS: Found 'In Queue' list: {list_id}")
    else:
        print(f"FAILED: Could not find 'In Queue' list on board {TRELLO_BOARD_APPOINTMENTS}")
        print("Attempting to list all lists on the board...")

        import requests
        try:
            url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_APPOINTMENTS}/lists"
            params = {"key": TRELLO_API_KEY, "token": TRELLO_API_TOKEN}
            response = requests.get(url, params=params)
            response.raise_for_status()
            lists = response.json()

            if lists:
                print(f"\nAvailable lists on board:")
                for list_item in lists:
                    closed = " (archived)" if list_item.get("closed") else ""
                    print(f"  - {list_item['name']}{closed}")
            else:
                print("No lists found on board!")
        except Exception as e:
            print(f"Error fetching lists: {e}")
else:
    print("FAILED: Missing Trello credentials or board ID")

# Test 5: Simulate Trello card creation
print("\n\n[5] Testing Trello Card Creation")
print("-" * 80)
if TRELLO_BOARD_APPOINTMENTS and TRELLO_API_KEY and TRELLO_API_TOKEN:
    from trello_tools import create_appointment_card

    # Use the parsed date/time from test 1
    success = create_appointment_card(
        patient_name="Sergii Vakulenko",
        doctor_name="Dr. Dalla McDer",
        appointment_date=parsed['appointment_date'] or "2026-07-30",
        appointment_time=parsed['appointment_time'] or "12:34",
        reason="Sight issue",
        patient_email="test@test.com",
        patient_id="P002"
    )

    if success:
        print("SUCCESS: Trello card created!")
    else:
        print("FAILED: Trello card creation failed - check errors above")
else:
    print("FAILED: Cannot test card creation - missing Trello configuration")

print("\n" + "=" * 80)
print("Debug Report Complete")
print("=" * 80)
