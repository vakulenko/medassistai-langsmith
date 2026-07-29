#!/usr/bin/env python
"""
Test Trello card creation functionality.

This script tests creating appointment and fraud cards on Trello.
"""

import os
from dotenv import load_dotenv
from trello_tools import create_appointment_card, create_fraud_card, get_list_id

load_dotenv()

def test_lists_exist():
    """Test that both boards have 'In Queue' lists."""
    print("=" * 70)
    print("Testing Trello List Availability")
    print("=" * 70)
    print()

    appointments_board = os.getenv("TRELLO_BOARD_APPOINTMENTS")
    tickets_board = os.getenv("TRELLO_BOARD_TICKETS")

    print(f"Appointments Board ID: {appointments_board}")
    list_id = get_list_id(appointments_board, "In Queue")
    if list_id:
        print(f"  -> 'In Queue' list found: {list_id}")
    else:
        print("  -> ERROR: 'In Queue' list not found!")
        return False

    print()
    print(f"Tickets Board ID: {tickets_board}")
    list_id = get_list_id(tickets_board, "In Queue")
    if list_id:
        print(f"  -> 'In Queue' list found: {list_id}")
    else:
        print("  -> ERROR: 'In Queue' list not found!")
        return False

    print()
    return True


def test_appointment_card():
    """Test creating an appointment card."""
    print("=" * 70)
    print("Testing Appointment Card Creation")
    print("=" * 70)
    print()

    success = create_appointment_card(
        patient_name="John Smith",
        doctor_name="Dr. Willi Bedna",
        appointment_date="2026-08-15",
        appointment_time="14:30",
        reason="Regular checkup",
        patient_email="john.smith@example.com"
    )

    if success:
        print("SUCCESS: Appointment card created!")
        return True
    else:
        print("FAILED: Could not create appointment card")
        return False


def test_fraud_card():
    """Test creating a fraud alert card."""
    print()
    print("=" * 70)
    print("Testing Fraud Card Creation")
    print("=" * 70)
    print()

    success = create_fraud_card(
        patient_name="Jane Doe",
        fraud_type="Suspicious Pattern",
        reason="Name too short (length < 3 chars)",
        session_id="test-session-123",
        patient_email="jane@example.com"
    )

    if success:
        print("SUCCESS: Fraud card created!")
        return True
    else:
        print("FAILED: Could not create fraud card")
        return False


def main():
    print()
    print("MedAssistAI - Trello Integration Test")
    print()

    results = []

    # Test 1: Lists exist
    if test_lists_exist():
        results.append(("List Availability", True))
    else:
        results.append(("List Availability", False))
        print()
        print("Cannot proceed with card creation tests without valid lists.")
        return

    # Test 2: Appointment card
    if test_appointment_card():
        results.append(("Appointment Card", True))
    else:
        results.append(("Appointment Card", False))

    # Test 3: Fraud card
    if test_fraud_card():
        results.append(("Fraud Card", True))
    else:
        results.append(("Fraud Card", False))

    # Summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print()

    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")

    print()
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed. Check the output above for details.")

    print()


if __name__ == "__main__":
    main()
