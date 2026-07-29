"""
Trello MCP Tools for LangGraph

Tools for creating appointment and fraud cards on Trello boards.
These tools are used by the agent to track appointments and fraud cases.
"""

import requests
from typing import Optional
from config import TRELLO_API_KEY, TRELLO_API_TOKEN, TRELLO_BOARD_APPOINTMENTS, TRELLO_BOARD_TICKETS


def get_trello_headers():
    """Get headers for Trello API requests."""
    return {
        "Authorization": f"OAuth oauth_consumer_key=\"{TRELLO_API_KEY}\", oauth_token=\"{TRELLO_API_TOKEN}\"",
        "Accept": "application/json"
    }


def get_list_id(board_id: str, list_name: str = "In Queue") -> Optional[str]:
    """Get the list ID from a board by name."""
    try:
        url = f"https://api.trello.com/1/boards/{board_id}/lists"
        params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_API_TOKEN
        }
        response = requests.get(url, params=params)
        response.raise_for_status()

        lists = response.json()
        for list_item in lists:
            if list_item["name"].lower() == list_name.lower() and not list_item.get("closed", False):
                return list_item["id"]

        return None
    except Exception as e:
        print(f"Error getting list ID: {str(e)}")
        return None


def create_appointment_card(
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    reason: str,
    patient_email: Optional[str] = None,
    patient_id: Optional[str] = None
) -> bool:
    """
    Create an appointment card on the "In Queue" list of Appointments board.

    Args:
        patient_name: Patient's full name
        doctor_name: Doctor's name
        appointment_date: Appointment date
        appointment_time: Appointment time
        reason: Reason for appointment
        patient_email: Patient's email (optional)

    Returns:
        True if card created successfully, False otherwise
    """
    try:
        list_id = get_list_id(TRELLO_BOARD_APPOINTMENTS, "In Queue")
        if not list_id:
            print("Could not find 'In Queue' list on Appointments board")
            return False

        # Build card description
        description = f"""Patient ID: {patient_id or 'Not provided'}
Patient: {patient_name}
Doctor: {doctor_name}
Date: {appointment_date}
Time: {appointment_time}
Reason: {reason}"""

        if patient_email:
            description += f"\nEmail: {patient_email}"

        # Create card
        url = "https://api.trello.com/1/cards"
        params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_API_TOKEN,
            "idList": list_id,
            "name": f"{patient_name} - {doctor_name}",
            "desc": description
        }

        response = requests.post(url, params=params)
        response.raise_for_status()

        print(f"Created appointment card for {patient_name}")
        return True

    except Exception as e:
        print(f"Error creating appointment card: {str(e)}")
        return False


def create_fraud_card(
    patient_name: str,
    fraud_type: str,
    reason: str,
    session_id: str,
    patient_email: Optional[str] = None
) -> bool:
    """
    Create a fraud card on the "In Queue" list of Tickets board.

    Args:
        patient_name: Patient's full name (potentially fraudulent)
        fraud_type: Type of fraud detected
        reason: Reason for fraud suspicion
        session_id: Session ID for tracing
        patient_email: Patient's email (optional)

    Returns:
        True if card created successfully, False otherwise
    """
    try:
        list_id = get_list_id(TRELLO_BOARD_TICKETS, "In Queue")
        if not list_id:
            print("Could not find 'In Queue' list on Tickets board")
            return False

        # Build card description
        description = f"""Type: Fraud Detection
Patient Name: {patient_name}
Fraud Type: {fraud_type}
Reason: {reason}
Session ID: {session_id}"""

        if patient_email:
            description += f"\nEmail: {patient_email}"

        # Create card
        url = "https://api.trello.com/1/cards"
        params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_API_TOKEN,
            "idList": list_id,
            "name": f"🚨 Fraud: {patient_name}",
            "desc": description,
            "labels": ["red"]  # Add red label for fraud
        }

        response = requests.post(url, params=params)
        response.raise_for_status()

        print(f"Created fraud card for {patient_name}")
        return True

    except Exception as e:
        print(f"Error creating fraud card: {str(e)}")
        return False


# Tool definitions for LangGraph
TRELLO_TOOLS = [
    {
        "name": "create_appointment_card",
        "description": "Create an appointment card on Trello when user requests to book appointment",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name": {"type": "string", "description": "Patient's full name"},
                "doctor_name": {"type": "string", "description": "Doctor's name"},
                "appointment_date": {"type": "string", "description": "Appointment date (YYYY-MM-DD)"},
                "appointment_time": {"type": "string", "description": "Appointment time (HH:MM)"},
                "reason": {"type": "string", "description": "Reason for appointment"},
                "patient_email": {"type": "string", "description": "Patient's email (optional)"}
            },
            "required": ["patient_name", "doctor_name", "appointment_date", "appointment_time", "reason"]
        }
    },
    {
        "name": "create_fraud_card",
        "description": "Create a fraud alert card on Trello when suspicious identity is detected",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name": {"type": "string", "description": "Patient's full name"},
                "fraud_type": {"type": "string", "description": "Type of fraud (e.g., identity mismatch, suspicious pattern)"},
                "reason": {"type": "string", "description": "Reason for fraud suspicion"},
                "session_id": {"type": "string", "description": "Session ID for tracing"},
                "patient_email": {"type": "string", "description": "Patient's email (optional)"}
            },
            "required": ["patient_name", "fraud_type", "reason", "session_id"]
        }
    }
]
