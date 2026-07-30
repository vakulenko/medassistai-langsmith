"""Individual agent implementations for multi-agent architecture."""

from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from state import Intent, ChatState
from intent_detector import _extract_text
from patient_validator import check_specialization_available, validate_patient_id
from date_time_parser import parse_date_time
from config import DOCTOR_PROFILES
import json
import re

try:
    from rag_vector_db import initialize_rag_db
except Exception as e:
    initialize_rag_db = None


class IntentDetectionAgent:
    """Agent responsible for detecting user intent."""

    INTENT_PROMPT = ChatPromptTemplate.from_template("""
Analyze the user's message and determine their intent for booking a doctor appointment.
Think through the message carefully to understand what the user wants.

User message: {user_input}
Conversation context: {conversation_context}

Determine the intent from these options:
- book_appointment: User wants to book an appointment with a doctor
- view_doctors: User wants to see available doctors
- check_availability: User wants to check doctor availability
- cancel_appointment: User wants to cancel an appointment
- general_info: User is asking general questions about the service
- unknown: Cannot determine the intent

Consider context clues from the conversation history.
Respond with ONLY the intent name (e.g., "book_appointment"), nothing else.
""")

    def execute(self, state: ChatState) -> ChatState:
        """Detect intent from user input."""
        llm = get_llm()
        chain = self.INTENT_PROMPT | llm

        conversation_context = " ".join(
            [msg.get("content", "") for msg in state.conversation_history[-3:]]
        )

        response = chain.invoke({
            "user_input": state.user_input,
            "conversation_context": conversation_context
        })

        intent_text = _extract_text(response).strip().lower()

        try:
            state.detected_intent = Intent(intent_text)
        except ValueError:
            state.detected_intent = Intent.UNKNOWN

        # Extract patient ID if present
        from intent_detector import extract_patient_id
        patient_id = extract_patient_id(state.user_input)
        if patient_id:
            state.patient_id = patient_id

        print(f"[IntentAgent] Detected intent: {state.detected_intent}")
        return state


class ExtractionAgent:
    """Agent responsible for extracting and validating information."""

    EXTRACTION_PROMPT = ChatPromptTemplate.from_template("""
You are an expert medical information extraction agent. Extract appointment booking information
from the user's message with high accuracy.

IMPORTANT RULES:
- doctor_name should ONLY be extracted if the user explicitly names a specific doctor
- If user mentions a specialization (like "psychiatry", "eye doctor") instead, use null for doctor_name
- specialization should capture the medical specialty requested
- Validate date and time formats
- Extract or infer patient information when present

User message: {user_input}
Conversation context: {conversation_context}

Extract the following information if present (return as JSON):
{{
  "patient_id": "Patient ID (like P001, P002, etc.) or null",
  "patient_name": "Patient's full name or null",
  "patient_email": "Patient's email address or null",
  "doctor_name": "Preferred doctor's full name (null if only specialization mentioned) or null",
  "appointment_date": "Preferred appointment date (YYYY-MM-DD format) or null",
  "appointment_time": "Preferred appointment time (HH:MM format) or null",
  "reason": "Reason for appointment/chief complaint or null",
  "specialization": "Required doctor specialization (like psychiatry, cardiology, etc.) or null"
}}

Return ONLY valid JSON, no additional text.
""")

    def _extract_specialization_from_input(self, text: str) -> str:
        """Extract specialization from user input as fallback."""
        specializations = [
            "ophthalmologist", "ophthalmology", "eye", "vision", "sight",
            "cardiologist", "cardiology", "heart",
            "orthopedist", "orthopedics", "spine", "bone",
            "pediatrician", "pediatrics", "children",
            "dermatologist", "dermatology", "skin",
            "psychiatrist", "psychiatry", "therapist", "therapy", "mental",
            "neurologist", "neurology", "brain",
            "surgeon", "surgery",
            "internist", "internal medicine", "general practice",
        ]

        text_lower = text.lower()
        for spec in specializations:
            if spec in text_lower:
                return spec
        return None

    def execute(self, state: ChatState) -> ChatState:
        """Extract information from user input."""
        llm = get_llm()
        chain = self.EXTRACTION_PROMPT | llm

        conversation_context = " ".join(
            [msg.get("content", "") for msg in state.conversation_history[-3:]]
        )

        response = chain.invoke({
            "user_input": state.user_input,
            "conversation_context": conversation_context
        })

        content = _extract_text(response)
        extracted_info = dict(state.extracted_info) if state.extracted_info else {}

        try:
            json_content = content
            if "```" in content:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    json_content = json_match.group(1)

            new_info = json.loads(json_content)
            print(f"[ExtractionAgent] Extracted: {new_info}")

            # Merge new info with existing (new takes precedence, but preserve non-null values)
            for key, value in new_info.items():
                if value is not None:
                    extracted_info[key] = value

            # Parse dates/times
            date_time_result = parse_date_time(state.user_input)
            if date_time_result.get("appointment_date"):
                extracted_info["appointment_date"] = date_time_result["appointment_date"]
            elif "tomorrow" in state.user_input.lower() and not extracted_info.get("appointment_date"):
                from datetime import datetime, timedelta
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                extracted_info["appointment_date"] = tomorrow

            if date_time_result.get("appointment_time"):
                extracted_info["appointment_time"] = date_time_result["appointment_time"]
            elif not extracted_info.get("appointment_time"):
                time_pattern = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', state.user_input)
                if time_pattern:
                    hour = int(time_pattern.group(1))
                    minute = time_pattern.group(2)
                    period = time_pattern.group(3)

                    if period and period.upper() == "PM" and hour != 12:
                        hour += 12
                    elif period and period.upper() == "AM" and hour == 12:
                        hour = 0

                    extracted_info["appointment_time"] = f"{hour:02d}:{minute}"

            # Fallback: extract patient name from input
            if not extracted_info.get("patient_name"):
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

            if not state.patient_id and extracted_info.get("patient_id"):
                state.patient_id = extracted_info["patient_id"]

        except json.JSONDecodeError:
            print("[ExtractionAgent] Failed to parse JSON response")
            pass

        return state


class PatientValidationAgent:
    """Agent responsible for validating patient data and checking availability."""

    def execute(self, state: ChatState) -> ChatState:
        """Validate patient data and extract availability info."""
        if state.detected_intent != Intent.BOOK_APPOINTMENT:
            return state

        state.use_rag_context = True
        rag_db = None

        try:
            if initialize_rag_db:
                rag_db = initialize_rag_db()
        except Exception as e:
            print(f"[PatientValidationAgent] RAG initialization failed: {e}")

        extracted = state.extracted_info or {}
        specialization = extracted.get("specialization") or state.requested_specialization
        doctor_name = extracted.get("doctor_name")

        # Fallback: extract specialization from input
        if not specialization:
            agent = ExtractionAgent()
            specialization = agent._extract_specialization_from_input(state.user_input)

        if specialization and rag_db:
            print(f"[PatientValidationAgent] Checking specialization: {specialization}")
            if specialization != state.requested_specialization:
                state.requested_specialization = specialization
                has_available, doctors = check_specialization_available(specialization, rag_db)
                state.has_available_doctor = has_available
                print(f"[PatientValidationAgent] Available doctors: {doctors}")
                if has_available and doctors and not doctor_name:
                    extracted["doctor_name"] = doctors[0]
                    state.extracted_info = extracted

        # Validate patient ID if provided
        if state.patient_id and not state.patient_not_found and not state.is_deceased_patient:
            print(f"[PatientValidationAgent] Validating patient ID: {state.patient_id}")
            try:
                if rag_db:
                    patient_data = rag_db.get_patient_info(state.patient_id)
                    if patient_data:
                        patient_exists, is_deceased = validate_patient_id(state.patient_id, patient_data)
                        if not patient_exists:
                            print(f"[PatientValidationAgent] Patient not found")
                            state.patient_not_found = True
                            state.should_add_patient = True
                        if is_deceased:
                            print(f"[PatientValidationAgent] Patient marked as deceased")
                            state.is_deceased_patient = True
                    else:
                        print(f"[PatientValidationAgent] No patient data found")
                        state.patient_not_found = True
                        state.should_add_patient = True
            except Exception as e:
                print(f"[PatientValidationAgent] Validation error: {e}")
                state.patient_not_found = True
                state.should_add_patient = True

        return state


class FraudDetectionAgent:
    """Agent responsible for detecting fraudulent patterns."""

    def execute(self, state: ChatState) -> ChatState:
        """Detect fraudulent patterns."""
        extracted = state.extracted_info or {}

        print(f"[FraudDetectionAgent] Checking for fraud patterns")

        # Simple pattern checks
        if extracted.get("patient_name") and len(extracted.get("patient_name", "")) < 3:
            print(f"[FraudDetectionAgent] Suspicious: Short patient name")
            state.fraud_score = 0.7
            from trello_tools import create_fraud_card
            create_fraud_card(
                patient_name=extracted.get("patient_name", "Unknown"),
                fraud_type="Data validation",
                reason="Suspiciously short patient name",
                session_id=extracted.get("session_id", "unknown"),
                patient_email=extracted.get("patient_email")
            )

        print(f"[FraudDetectionAgent] Fraud check complete")
        return state


class ResponseGenerationAgent:
    """Agent responsible for generating contextual responses."""

    BOOKING_PROMPT = ChatPromptTemplate.from_template("""
You are a medical appointment booking assistant for MedAssistAI.

PATIENT IDENTIFICATION:
- Patient ID: {patient_id}
- Patient Name: {patient_name}
- Patient Email: {patient_email}
- Patient Status: {patient_status}

APPOINTMENT DETAILS:
- Requested Doctor: {doctor_name}
- Requested Date: {appointment_date}
- Requested Time: {appointment_time}
- Reason for Visit: {appointment_reason}

SPECIALIZATION CHECK:
- Requested Specialization: {specialization}
- Available: {has_doctor}

DOCTOR & PATIENT CONTEXT:
{doctor_context}
{patient_context}

INSTRUCTIONS:
1. Patient ID must be provided - ask for it if missing
2. Prioritize contextual information from doctor profiles and patient data
3. If requested specialization is NOT available, explain we cannot help
4. Once all details are confirmed, ask explicit approval to proceed
5. Never proceed without explicit user confirmation
6. If patient status is "New (not in system)", mention they will be registered

User message: {user_input}
Conversation: {conversation_history}

Respond helpfully and professionally.
""")

    GENERAL_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful medical appointment booking assistant for MedAssistAI.

User message: {user_input}
Available Doctors: {available_doctors}

Relevant Information:
{rag_context}

Conversation history: {conversation_history}

Provide a helpful response about the service, doctors, or general information.
Use the available information to answer questions about doctors and services.
Be warm, professional, and guide the user towards booking an appointment if relevant.
""")

    PATIENT_NOT_FOUND_PROMPT = ChatPromptTemplate.from_template("""
A new patient is trying to book an appointment. They provided:
- Patient Name: {patient_name}
- Patient ID: {patient_id}
- Doctor/Specialization: {doctor_name}
- Requested Date: {appointment_date}
- Requested Time: {appointment_time}
- Reason: {reason}

This patient is NOT in our system yet. We will add them, but first ask for confirmation
to proceed with the appointment booking. The patient will be added to our system as a
new patient once booking is confirmed.

Generate a professional response that:
1. Confirms we'll add them as a new patient
2. Shows the doctor/specialization we found for them
3. Asks if they want to proceed with the booking
4. Lists what we have for them
""")

    def execute(self, state: ChatState) -> ChatState:
        """Generate response based on state."""
        llm = get_llm()
        available_doctors = list(DOCTOR_PROFILES.keys())

        rag_db = None
        if initialize_rag_db:
            try:
                rag_db = initialize_rag_db()
            except Exception as e:
                print(f"[ResponseGenerationAgent] RAG init failed: {e}")

        if state.detected_intent == Intent.BOOK_APPOINTMENT:
            if state.patient_not_found and not state.appointment_ready_for_confirmation:
                prompt = self.PATIENT_NOT_FOUND_PROMPT
                extracted = state.extracted_info
                response = llm.invoke(prompt.format_prompt(
                    patient_name=extracted.get("patient_name", "Unknown"),
                    patient_id=state.patient_id or "Not provided",
                    doctor_name=extracted.get("doctor_name", "Not specified"),
                    appointment_date=extracted.get("appointment_date", "Not specified"),
                    appointment_time=extracted.get("appointment_time", "Not specified"),
                    reason=extracted.get("reason", "General checkup")
                ).messages)
            else:
                prompt = self.BOOKING_PROMPT
                extracted = state.extracted_info

                doctor_context = ""
                patient_context = ""

                if state.use_rag_context and rag_db:
                    doctor_name = extracted.get("doctor_name", "")
                    if doctor_name:
                        doc_info = rag_db.get_doctor_info(doctor_name)
                        doctor_context = doc_info or "Doctor information from records"

                    if state.patient_id:
                        patient_info = rag_db.get_patient_info(state.patient_id)
                        patient_context = patient_info or "Patient information from records"
                    elif extracted.get("patient_name"):
                        patient_info = rag_db.get_patient_info(extracted.get("patient_name"))
                        patient_context = patient_info or "Patient information from records"

                patient_status = "New (not in system)" if state.patient_not_found else "Existing patient"
                appointment_date = extracted.get("appointment_date", "Not specified")
                appointment_time = extracted.get("appointment_time", "Not specified")

                if appointment_date and appointment_date.lower() in ["tomorrow", "not specified"]:
                    from date_time_parser import parse_date_time
                    parsed = parse_date_time(state.user_input)
                    if parsed.get("appointment_date"):
                        appointment_date = parsed["appointment_date"]

                if appointment_time and (":" not in appointment_time or appointment_time.lower() in ["not specified"]):
                    from date_time_parser import parse_date_time
                    parsed = parse_date_time(state.user_input)
                    if parsed.get("appointment_time"):
                        appointment_time = parsed["appointment_time"]

                response = llm.invoke(prompt.format_prompt(
                    patient_id=state.patient_id or "Not provided",
                    patient_name=extracted.get("patient_name", "Not provided"),
                    patient_email=extracted.get("patient_email", "Not provided"),
                    patient_status=patient_status,
                    doctor_name=extracted.get("doctor_name", "Not specified"),
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    appointment_reason=extracted.get("reason", "Not specified"),
                    specialization=state.requested_specialization or "Not specified",
                    has_doctor="Yes" if state.has_available_doctor else "No",
                    available_doctors=", ".join(available_doctors),
                    doctor_context=doctor_context,
                    patient_context=patient_context,
                    user_input=state.user_input,
                    conversation_history="\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in state.conversation_history[-3:]])
                ).messages)
        else:
            prompt = self.GENERAL_PROMPT
            rag_context = ""
            if rag_db:
                context_list = rag_db.retrieve_relevant_context(state.user_input, top_k=3)
                rag_context = "\n".join(context_list) if context_list else "General information about our medical services"

            response = llm.invoke(prompt.format_prompt(
                user_input=state.user_input,
                available_doctors=", ".join(available_doctors),
                rag_context=rag_context,
                conversation_history="\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in state.conversation_history[-3:]])
            ).messages)

        state.last_response = _extract_text(response)
        print(f"[ResponseGenerationAgent] Generated response")
        return state


class ConfirmationValidationAgent:
    """Agent responsible for validating booking confirmation."""

    def execute(self, state: ChatState) -> ChatState:
        """Validate confirmation response."""
        user_input_lower = state.user_input.lower().strip()

        # Direct keyword matching
        if any(keyword in user_input_lower for keyword in ["yes", "approve", "confirm", "agree", "ok", "okay", "go ahead"]):
            state.booking_confirmed = True
            print("[ConfirmationValidationAgent] Booking confirmed by user")
            return state

        if any(keyword in user_input_lower for keyword in ["no", "reject", "cancel", "decline", "stop"]):
            print("[ConfirmationValidationAgent] Booking rejected by user")
            return state

        print("[ConfirmationValidationAgent] Unclear response")
        return state
