"""Orchestrator for multi-agent system using supervisor pattern."""

from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from state import Intent, ChatState
from agents import (
    IntentDetectionAgent,
    ExtractionAgent,
    PatientValidationAgent,
    FraudDetectionAgent,
    ResponseGenerationAgent,
    ConfirmationValidationAgent
)
from intent_detector import _extract_text


class AgentOrchestrator:
    """Supervisor that coordinates multi-agent execution."""

    def __init__(self):
        self.intent_agent = IntentDetectionAgent()
        self.extraction_agent = ExtractionAgent()
        self.validation_agent = PatientValidationAgent()
        self.fraud_agent = FraudDetectionAgent()
        self.response_agent = ResponseGenerationAgent()
        self.confirmation_agent = ConfirmationValidationAgent()

    def execute_workflow(self, state: ChatState) -> ChatState:
        """Execute the multi-agent workflow."""
        print("\n" + "="*80)
        print("[ORCHESTRATOR] Starting multi-agent workflow")
        print("="*80)

        # Stage 1: Intent Detection
        print("\n[ORCHESTRATOR] Stage 1: Intent Detection")
        state = self.intent_agent.execute(state)

        # Stage 2: Information Extraction
        print("\n[ORCHESTRATOR] Stage 2: Information Extraction")
        state = self.extraction_agent.execute(state)

        # Stage 3: Fraud Detection (early check)
        print("\n[ORCHESTRATOR] Stage 3: Fraud Detection")
        state = self.fraud_agent.execute(state)

        # Stage 4: Patient Validation (only for booking)
        if state.detected_intent == Intent.BOOK_APPOINTMENT:
            print("\n[ORCHESTRATOR] Stage 4: Patient Validation")
            state = self.validation_agent.execute(state)

        # Stage 5: Set confirmation flags
        print("\n[ORCHESTRATOR] Stage 5: Setting Confirmation Flags")
        state = self._set_confirmation_flags(state)

        # Stage 6: Determine routing
        print("\n[ORCHESTRATOR] Stage 6: Determining Routing")
        routing_decision = self._determine_routing(state)
        print(f"[ORCHESTRATOR] Routing decision: {routing_decision}")

        # Stage 7: Route to appropriate handler
        print("\n[ORCHESTRATOR] Stage 7: Route Handler")
        if routing_decision == "ask_for_info":
            print("[ORCHESTRATOR] Routing to: ask_for_info")
            state = self.response_agent.execute(state)
        elif routing_decision == "ask_for_confirmation":
            print("[ORCHESTRATOR] Routing to: ask_for_confirmation")
            state = self.response_agent.execute(state)
        elif routing_decision == "confirmation_response":
            print("[ORCHESTRATOR] Routing to: confirmation_response")
            state = self.confirmation_agent.execute(state)
            if state.booking_confirmed:
                print("[ORCHESTRATOR] Booking confirmed - creating appointment")
                state = self._create_appointment(state)
            else:
                print("[ORCHESTRATOR] Booking not confirmed or rejected")
                state.last_response = "Booking cancelled. Feel free to contact us if you change your mind."
        else:
            print("[ORCHESTRATOR] Routing to: generate_response")
            state = self.response_agent.execute(state)

        print("\n" + "="*80)
        print("[ORCHESTRATOR] Workflow complete")
        print("="*80 + "\n")

        return state

    def _set_confirmation_flags(self, state: ChatState) -> ChatState:
        """Set confirmation flags based on state."""
        if state.appointment_ready_for_confirmation:
            return state

        if state.detected_intent == Intent.BOOK_APPOINTMENT:
            # Check for pending confirmations
            if state.is_deceased_patient:
                state.appointment_ready_for_confirmation = True

            # Check if all required info is present
            required_fields = ["patient_name", "patient_email", "doctor_name", "appointment_date", "appointment_time"]
            missing_fields = [f for f in required_fields if not state.extracted_info.get(f)]

            # If patient not found AND we have patient name + email + doctor, go to confirmation
            if state.patient_not_found:
                if state.extracted_info.get("patient_name") and state.extracted_info.get("patient_email"):
                    state.appointment_ready_for_confirmation = True
            elif state.patient_id and not missing_fields:
                # All info present - ask for explicit confirmation
                state.appointment_ready_for_confirmation = True

        return state

    def _determine_routing(self, state: ChatState) -> str:
        """Determine next routing decision."""
        # Check for pending confirmations
        if state.appointment_ready_for_confirmation:
            return "ask_for_confirmation"

        if state.detected_intent == Intent.BOOK_APPOINTMENT:
            # Check if specialization is not available
            if state.requested_specialization and not state.has_available_doctor:
                return "end"

            # Check if all required info is present
            required_fields = ["patient_name", "patient_email", "doctor_name", "appointment_date", "appointment_time"]
            missing_fields = [f for f in required_fields if not state.extracted_info.get(f)]

            # Patient ID is required
            if not state.patient_id:
                return "ask_for_info"

            # If patient not found AND we have patient name + email + doctor, go to confirmation
            if state.patient_not_found:
                if state.extracted_info.get("patient_name") and state.extracted_info.get("patient_email"):
                    return "ask_for_confirmation"
                return "ask_for_info"

            if not missing_fields:
                # All info present - ask for explicit confirmation
                return "ask_for_confirmation"
            return "ask_for_info"

        return "generate_response"

    def _create_appointment(self, state: ChatState) -> ChatState:
        """Create appointment card on Trello."""
        from trello_tools import create_appointment_card, create_fraud_card, create_add_patient_card

        if state.is_deceased_patient:
            # Deceased patient: create fraud ticket
            create_fraud_card(
                patient_name=state.extracted_info.get("patient_name", "Unknown"),
                fraud_type="Deceased patient",
                reason=f"Booking attempt for deceased patient ID: {state.patient_id}",
                session_id=state.extracted_info.get("session_id", "unknown"),
                patient_email=state.extracted_info.get("patient_email")
            )
            state.booking_confirmed = True
            print("[ORCHESTRATOR] Deceased patient confirmed booking - fraud ticket created")
            return state

        # Normal booking: create appointment card
        extracted = state.extracted_info or {}

        print(f"\n{'='*80}")
        print(f"[ORCHESTRATOR] Creating appointment card")
        print(f"[ORCHESTRATOR] Patient Name: {extracted.get('patient_name', 'Unknown')}")
        print(f"[ORCHESTRATOR] Doctor Name: {extracted.get('doctor_name', 'Unknown')}")
        print(f"[ORCHESTRATOR] Date: {extracted.get('appointment_date', 'Unknown')}")
        print(f"[ORCHESTRATOR] Time: {extracted.get('appointment_time', 'Unknown')}")
        print(f"[ORCHESTRATOR] Patient ID: {state.patient_id}")
        print(f"{'='*80}\n")

        if extracted or state.patient_id:
            success = create_appointment_card(
                patient_name=extracted.get("patient_name", "Unknown"),
                doctor_name=extracted.get("doctor_name", "Unknown"),
                appointment_date=extracted.get("appointment_date", "Unknown"),
                appointment_time=extracted.get("appointment_time", "Unknown"),
                reason=extracted.get("reason", "General checkup"),
                patient_email=extracted.get("patient_email"),
                patient_id=state.patient_id
            )
            print(f"[ORCHESTRATOR] Appointment card creation result: {success}\n")

            # If patient not found in system, create add-patient card as well
            if state.patient_not_found:
                print(f"[ORCHESTRATOR] Creating add-patient card for {extracted.get('patient_name', 'Unknown')}")
                success_patient_card = create_add_patient_card(
                    patient_name=extracted.get("patient_name", "Unknown"),
                    patient_email=extracted.get("patient_email"),
                    patient_id=state.patient_id,
                    notes=f"New patient booking: {extracted.get('reason', 'General')}"
                )
                print(f"[ORCHESTRATOR] Add-patient card creation result: {success_patient_card}\n")

            state.booking_confirmed = True
            print(f"[ORCHESTRATOR] Booking confirmed for {extracted.get('patient_name', 'Unknown')}")
        else:
            print(f"[ORCHESTRATOR] ERROR: No extracted info available for card creation")

        return state
