# Multi-Agent Architecture for MedAssistAI

## Overview

The application has been converted from a single-pipeline approach to a **multi-agent supervisor pattern** where each specialized task is handled by an independent LLM agent.

## Architecture Components

### 1. Individual Agents

Each agent is a specialized component with clear responsibilities:

#### **IntentDetectionAgent**
- **Purpose**: Analyzes user input to determine their intent
- **Intents**: 
  - `book_appointment` - User wants to book an appointment
  - `view_doctors` - User wants to see available doctors
  - `check_availability` - User wants to check doctor availability
  - `cancel_appointment` - User wants to cancel an appointment
  - `general_info` - User is asking general questions
  - `unknown` - Cannot determine intent
- **Output**: Sets `state.detected_intent`
- **Uses**: Conversation history for context

#### **ExtractionAgent**
- **Purpose**: Extracts structured data from user input
- **Extracts**:
  - `patient_id` - Patient identifier (P001, P002, etc.)
  - `patient_name` - Full name of patient
  - `patient_email` - Patient email address
  - `doctor_name` - Specific doctor (if named)
  - `appointment_date` - Date in YYYY-MM-DD format
  - `appointment_time` - Time in HH:MM format
  - `reason` - Reason for appointment
  - `specialization` - Medical specialty (cardiology, ophthalmology, etc.)
- **Output**: Populates `state.extracted_info`
- **Features**: 
  - Merges with existing extracted data (preserves prior context)
  - Fallback date/time parsing
  - Pattern-based name extraction

#### **PatientValidationAgent**
- **Purpose**: Validates patient data and checks doctor availability
- **Responsibilities**:
  - Validates patient ID against database
  - Checks if specialization is available
  - Determines if patient exists in system
  - Detects if patient is marked as deceased
  - Auto-assigns available doctor if only specialization provided
- **Output**: 
  - Sets `state.patient_not_found`
  - Sets `state.is_deceased_patient`
  - Sets `state.has_available_doctor`
  - Sets `state.requested_specialization`
- **Triggers**: Only runs for `BOOK_APPOINTMENT` intent
- **Uses**: RAG vector database for patient/doctor lookups

#### **FraudDetectionAgent**
- **Purpose**: Identifies suspicious patterns in booking requests
- **Detections**:
  - Suspiciously short patient names (< 3 characters)
  - Inconsistent patient data patterns
  - (Extensible for additional fraud rules)
- **Output**: Creates fraud cards on Trello if issues detected
- **Runs**: Early in pipeline, before response generation

#### **ResponseGenerationAgent**
- **Purpose**: Generates appropriate user-facing responses
- **Handles Three Scenarios**:
  1. **Booking Intent**: Uses detailed booking prompt with:
     - Patient/appointment details
     - Doctor and patient context from RAG
     - Specialization availability info
     - Instructions for confirmation flow
  2. **Patient Not Found**: Special prompt that:
     - Confirms patient will be added to system
     - Shows assigned doctor/specialization
     - Asks for confirmation to proceed
     - Lists what information was collected
  3. **General Intent**: General query response that:
     - Provides information about services
     - Lists available doctors
     - Guides toward booking if relevant
- **Output**: Sets `state.last_response`
- **Uses**: RAG context for relevant information

#### **ConfirmationValidationAgent**
- **Purpose**: Interprets user confirmation/rejection responses
- **Interprets**:
  - **Confirm**: "yes", "approve", "confirm", "agree", "ok", "okay", "go ahead"
  - **Reject**: "no", "reject", "cancel", "decline", "stop"
  - **Unclear**: Any other response
- **Output**: Sets `state.booking_confirmed` flag
- **Only Runs**: When in confirmation state

### 2. AgentOrchestrator (Supervisor)

The `AgentOrchestrator` coordinates all agents in a structured workflow:

```
Stage 1: Intent Detection
     ↓
Stage 2: Information Extraction
     ↓
Stage 3: Fraud Detection
     ↓
Stage 4: Patient Validation (if booking)
     ↓
Stage 5: Set Confirmation Flags
     ↓
Stage 6: Determine Routing Decision
     ↓
Stage 7: Execute Route Handler
     ├→ ask_for_info: Generate response
     ├→ ask_for_confirmation: Generate confirmation prompt
     ├→ confirmation_response: Validate confirmation & create appointment
     └→ generate_response: Generate general response
     ↓
   END
```

**Key Methods**:
- `execute_workflow()` - Orchestrates all stages
- `_set_confirmation_flags()` - Determines if ready for confirmation
- `_determine_routing()` - Routes to appropriate handler
- `_create_appointment()` - Creates Trello cards for confirmed bookings

### 3. Updated Graph (graph.py)

The LangGraph is simplified to a single node wrapping the orchestrator:

```python
StateGraph(ChatState)
    ↓
multi_agent_workflow node
    ├→ Calls AgentOrchestrator.execute_workflow()
    ├→ Orchestrator runs all stages internally
    └→ Returns updated state
    ↓
   END
```

This maintains LangGraph compatibility while delegating business logic to agents.

## State Management

The `ChatState` maintains:

### Core Fields
- `user_input: str` - Current user message
- `detected_intent: Intent` - Result from IntentDetectionAgent
- `extracted_info: dict` - Accumulated extracted data
- `conversation_history: List[dict]` - Full conversation
- `last_response: str` - Response to send to user

### Booking-Specific Fields
- `patient_id: Optional[str]` - Patient identifier
- `requested_specialization: Optional[str]` - Specialty being requested
- `has_available_doctor: bool` - Whether specialty has doctors available
- `appointment_ready_for_confirmation: bool` - Ready to ask user to confirm
- `booking_confirmed: bool` - User has confirmed booking
- `patient_not_found: bool` - Patient not in system
- `is_deceased_patient: bool` - Patient marked as deceased
- `use_rag_context: bool` - Whether to use RAG for context

## Data Flow

### Simple Information Request
```
User: "Tell me about ophthalmologists"
     ↓
Intent Agent: "general_info"
     ↓
Response Agent: Generates info about services
     ↓
Output: Response text
```

### Full Booking Flow
```
User: "I want to book with an ophthalmologist. I'm P001, John Smith, john@email.com, tomorrow at 2pm"
     ↓
Intent Agent: "book_appointment"
     ↓
Extraction Agent: {patient_id: P001, patient_name: John Smith, ...}
     ↓
Fraud Agent: Check for suspicious patterns
     ↓
Validation Agent: Validate patient P001, check ophthalmology availability
     ↓
Flag Setting: Check if all info present
     ↓
Router: "ask_for_confirmation" (if all info present)
     ↓
Response Agent: Generate confirmation prompt
     ↓
Output: "Please confirm your booking for Dr. X on [date] at [time]"

---

User: "Yes, confirm"
     ↓
Intent Agent: "unknown" (confirmation is standalone)
     ↓
Extraction Agent: No new info
     ↓
Router: "confirmation_response" (due to flag)
     ↓
Confirmation Agent: Validates "Yes"
     ↓
Orchestrator: Creates appointment card on Trello
     ↓
Output: "Booking confirmed!"
```

## Key Differences from Original Architecture

| Aspect | Original | Multi-Agent |
|--------|----------|------------|
| **Structure** | Single pipeline | Coordinated agents |
| **Node Design** | Monolithic functions | Specialized classes |
| **Reasoning** | Implicit in code | Explicit in LLM prompts |
| **Extensibility** | Add to pipeline | Add new agent class |
| **Testing** | Test full pipeline | Test agents independently |
| **Parallelization** | Limited | Agents can run in parallel (future) |
| **LLM Calls** | ~3 per request | ~5-6 per request (more reasoning) |

## Adding New Agents

To add a new agent:

1. **Create agent class** in `agents.py`:
```python
class MyAgent:
    PROMPT = ChatPromptTemplate.from_template("...")
    
    def execute(self, state: ChatState) -> ChatState:
        # Agent logic
        return state
```

2. **Add to orchestrator** in `agent_orchestrator.py`:
```python
def __init__(self):
    self.my_agent = MyAgent()
    
def execute_workflow(self, state):
    # Add stage
    state = self.my_agent.execute(state)
```

3. **Test independently** before integration.

## Debugging

Each agent logs at the [AgentName] prefix, e.g.:
- `[IntentAgent] Detected intent: ...`
- `[ExtractionAgent] Extracted: ...`
- `[PatientValidationAgent] Validating patient ID: ...`
- `[ORCHESTRATOR] Stage X: ...`

Full orchestrator flow is printed with `==` dividers for easy debugging.

## Files Modified

- ✅ `agents.py` - NEW: All individual agents
- ✅ `agent_orchestrator.py` - NEW: Supervisor orchestrator
- ✅ `graph.py` - MODIFIED: Simplified to single multi-agent node
- Original files preserved:
  - `intent_detector.py`
  - `info_extractor.py`
  - `response_generator.py`
  - `patient_validator.py`

## Performance Considerations

- Each agent makes at least one LLM call
- Total ~5-6 LLM calls per request (vs ~3 in original)
- Trade-off: More reasoning capability vs higher latency
- Future: Implement agent parallelization for independent stages

## Testing the System

```bash
# Run chatbot normally
python chatbot.py

# Test multi-agent workflow directly
python -c "
from graph import graph
from state import ChatState

test = ChatState(
    user_input='I want to book with an ophthalmologist, ID P001, John Smith, john@example.com',
    conversation_history=[],
    extracted_info={}
)
result = graph.invoke(test)
print(result['last_response'])
"
```
