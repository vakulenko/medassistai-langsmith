from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
import uuid

class Intent(str, Enum):
    BOOK_APPOINTMENT = "book_appointment"
    VIEW_DOCTORS = "view_doctors"
    CHECK_AVAILABILITY = "check_availability"
    GENERAL_INFO = "general_info"
    UNKNOWN = "unknown"

@dataclass
class Appointment:
    doctor_name: str
    date: str
    time: str
    reason: str
    patient_name: Optional[str] = None
    patient_email: Optional[str] = None

@dataclass
class ChatState:
    """State for the appointment booking chatbot."""
    messages: List[dict] = field(default_factory=list)
    user_input: str = ""
    detected_intent: Intent = Intent.UNKNOWN
    extracted_info: dict = field(default_factory=dict)
    appointment_details: Optional[Appointment] = None
    available_doctors: List[str] = field(default_factory=list)
    conversation_history: List[dict] = field(default_factory=list)
    booking_confirmed: bool = False
    last_response: str = ""
    patient_id: Optional[str] = None
    use_rag_context: bool = False
    requested_specialization: Optional[str] = None
    has_available_doctor: bool = False
    appointment_ready_for_confirmation: bool = False
    is_deceased_patient: bool = False
    patient_not_found: bool = False
    should_add_patient: bool = False

@dataclass
class Session:
    """Represents a chat session with its own context."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "New Session"
    chat_history: List[dict] = field(default_factory=list)
    conversation_history: List[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class SessionManager:
    """Manages multiple chat sessions."""

    @staticmethod
    def create_session(name: str = "New Session") -> Session:
        """Create a new session."""
        return Session(name=name)

    @staticmethod
    def get_session_display_name(session: Session) -> str:
        """Get display name with created time."""
        return f"{session.name} ({session.created_at.split()[1]})"
