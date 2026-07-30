from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from intent_detector import _extract_text
from patient_validator import check_specialization_available, validate_patient_id
from date_time_parser import parse_date_time
from state import Intent
import json
import re

def _extract_specialization_from_input(text: str) -> str:
    """Extract specialization from user input as fallback.

    Looks for keywords like: ophthalmologist, cardiologist, pediatrician, etc.
    """
    specializations = [
        "ophthalmologist", "ophthalmology", "eye", "vision", "sight",
        "cardiologist", "cardiology", "heart",
        "orthopedist", "orthopedics", "spine", "bone",
        "pediatrician", "pediatrics", "children",
        "dermatologist", "dermatology", "skin",
        "psychiatrist", "psychiatry", "mental",
        "neurologist", "neurology", "brain",
        "surgeon", "surgery",
        "internist", "internal medicine", "general practice",
    ]

    text_lower = text.lower()
    for spec in specializations:
        if spec in text_lower:
            return spec

    return None


EXTRACTION_PROMPT = ChatPromptTemplate.from_template("""
Extract appointment booking information from the user's message.

IMPORTANT:
- doctor_name should ONLY be extracted if the user explicitly names a specific doctor
- If user mentions a specialization (like "psychiatry", "eye doctor", etc.) instead of a doctor name, use null for doctor_name
- specialization should capture the medical specialty requested

User message: {user_input}
Conversation context: {conversation_context}

Extract the following information if present (return as JSON):
- patient_id: Patient ID (like P001, P002, etc.)
- patient_name: Patient's full name
- patient_email: Patient's email address
- doctor_name: Preferred doctor's full name (null if only specialization mentioned)
- appointment_date: Preferred appointment date (YYYY-MM-DD format)
- appointment_time: Preferred appointment time (HH:MM format)
- reason: Reason for appointment/chief complaint
- specialization: Required doctor specialization (like psychiatry, cardiology, ophthalmology, etc.)

For any missing information, use null.
Return ONLY valid JSON, no additional text.
""")


def extract_info(state):
    """Extract relevant appointment information from user input."""
    llm = get_llm()
    chain = EXTRACTION_PROMPT | llm

    conversation_context = " ".join([msg.get("content", "") for msg in state.conversation_history[-3:]])

    response = chain.invoke({
        "user_input": state.user_input,
        "conversation_context": conversation_context
    })

    content = _extract_text(response)

    # START with existing extracted info to preserve previous context
    extracted_info = dict(state.extracted_info) if state.extracted_info else {}

    try:
        # Extract JSON from markdown code blocks if needed
        json_content = content
        if "```" in content:
            # Extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)

        new_info = json.loads(json_content)

        # Debug: log what the LLM extracted
        print(f"\n[EXTRACTION] LLM returned: {new_info}")

        # Merge new info with existing (new info takes precedence)
        # But don't overwrite with null values - preserve existing data
        for key, value in new_info.items():
            if value is not None:
                extracted_info[key] = value

        # Parse natural language dates/times to strict format with silent failures
        date_time_result = parse_date_time(state.user_input)

        # Update if we got a parsed date
        if date_time_result.get("appointment_date"):
            extracted_info["appointment_date"] = date_time_result["appointment_date"]
        # Fallback: if we have "tomorrow" in input and no date, use simple calculation
        elif "tomorrow" in state.user_input.lower() and not extracted_info.get("appointment_date"):
            from datetime import datetime, timedelta
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            extracted_info["appointment_date"] = tomorrow

        # Update if we got a parsed time
        if date_time_result.get("appointment_time"):
            extracted_info["appointment_time"] = date_time_result["appointment_time"]
        # Fallback: extract time pattern like "12:34 PM" or "12:34"
        elif not extracted_info.get("appointment_time"):
            time_pattern = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', state.user_input)
            if time_pattern:
                hour = int(time_pattern.group(1))
                minute = time_pattern.group(2)
                period = time_pattern.group(3)

                # Convert to 24-hour format if AM/PM provided
                if period and period.upper() == "PM" and hour != 12:
                    hour += 12
                elif period and period.upper() == "AM" and hour == 12:
                    hour = 0

                extracted_info["appointment_time"] = f"{hour:02d}:{minute}"

        # Fallback: Extract patient name from input if LLM didn't get it
        if not extracted_info.get("patient_name"):
            # Look for patterns like "My name is X", "I'm X", "name: X"
            patterns = [
                r'(?:my\s+)?name\s+(?:is\s+)?([A-Za-z\s]+?)(?:;|,|\.|\s+(?:email|id|patient))',
                r"i'm\s+([A-Za-z\s]+?)(?:;|,|\.|\s+(?:email|id|patient))",
                r'(?:patient\s+)?name\s*:\s*([A-Za-z\s]+?)(?:;|,|\.)',
            ]
            for pattern in patterns:
                match = re.search(pattern, state.user_input, re.IGNORECASE)
                if match:
                    extracted_info["patient_name"] = match.group(1).strip().title()
                    break

        state.extracted_info = extracted_info

        # Extract patient ID from the extracted info if not already set
        if not state.patient_id and extracted_info.get("patient_id"):
            state.patient_id = extracted_info["patient_id"]

    except json.JSONDecodeError:
        # Keep existing extracted_info on JSON parse error
        pass

    # Determine if this request involves doctor/patient data (should use RAG)
    if state.detected_intent == Intent.BOOK_APPOINTMENT:
        state.use_rag_context = True

        # Initialize RAG DB for specialization checking
        rag_db = None
        try:
            from rag_vector_db import initialize_rag_db
            rag_db = initialize_rag_db()
        except Exception as e:
            pass

        # Check specialization availability using RAG data
        # Use previously detected specialization if available
        specialization = extracted_info.get("specialization") or state.requested_specialization
        doctor_name = extracted_info.get("doctor_name")

        # Fallback: If LLM didn't extract specialization, try to find it in user input
        if not specialization:
            specialization = _extract_specialization_from_input(state.user_input)

        if specialization and rag_db:
            # Only re-check if specialization is new (different from previous)
            if specialization != state.requested_specialization:
                state.requested_specialization = specialization
                has_available, doctors = check_specialization_available(specialization, rag_db)
                state.has_available_doctor = has_available
                print(f"\n[SPECIALIZATION] Requested: {specialization}")
                print(f"[SPECIALIZATION] Available doctors: {doctors}")
                print(f"[SPECIALIZATION] Current doctor_name: {doctor_name}")
                if has_available and doctors:
                    # Suggest the first available doctor
                    if not doctor_name:
                        print(f"[SPECIALIZATION] Assigning: {doctors[0]}")
                        extracted_info["doctor_name"] = doctors[0]
                        state.extracted_info = extracted_info
                    else:
                        print(f"[SPECIALIZATION] Doctor already set, not overwriting")
            else:
                # Use previously detected availability (don't re-check)
                print(f"[SPECIALIZATION] Using cached availability (same as before: {state.requested_specialization})")
                pass

        # Validate patient ID if provided (only validate if not already validated)
        if state.patient_id and not state.patient_not_found and not state.is_deceased_patient:
            print(f"\n[PATIENT LOOKUP] Validating patient ID: {state.patient_id}")
            try:
                from rag_vector_db import initialize_rag_db
                rag_db = initialize_rag_db()
                # Use direct patient lookup, not semantic search
                patient_data = rag_db.get_patient_info(state.patient_id)

                if patient_data:
                    print(f"[PATIENT LOOKUP] Found patient data, validating...")
                    patient_exists, is_deceased = validate_patient_id(state.patient_id, patient_data)
                    if not patient_exists:
                        # Patient ID not found in data
                        print(f"[PATIENT LOOKUP] Patient ID {state.patient_id} not found in system")
                        state.patient_not_found = True
                        state.should_add_patient = True
                    if is_deceased:
                        print(f"[PATIENT LOOKUP] Patient ID {state.patient_id} is marked deceased")
                        state.is_deceased_patient = True
                else:
                    # No patient data returned = patient not in system
                    print(f"[PATIENT LOOKUP] No patient data found for {state.patient_id} - patient not in system")
                    state.patient_not_found = True
                    state.should_add_patient = True
            except Exception as e:
                # If lookup fails, assume patient not in system
                print(f"[PATIENT LOOKUP] ERROR: {e} - assuming patient not in system")
                state.patient_not_found = True
                state.should_add_patient = True

    return state
