import streamlit as st
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent, SessionManager, Session
from config import DOCTOR_PROFILES
from langsmith_debug import initialize_langsmith_tracing, get_langsmith_project_url, log_agent_run
from rag_vector_db import initialize_rag_db

# Load environment variables
load_dotenv()

# Configure LangSmith for tracing
initialize_langsmith_tracing()

# Initialize RAG vector database
@st.cache_resource
def load_rag_data():
    """Load RAG data on app startup."""
    try:
        rag_db = initialize_rag_db()

        # Check if we need to reload data from Google Drive
        # (important for Streamlit Cloud deployment where cached DB might be stale)
        try:
            stats = rag_db.get_db_stats()
            document_count = stats.get("total_documents", 0)

            if document_count == 0:
                print("[RAG] Vector database is empty - reloading from Google Drive...")
                from load_rag_data import load_rag_data as load_rag_data_func
                load_rag_data_func(force_reload=False)
                rag_db = initialize_rag_db()  # Re-initialize to get fresh data
        except Exception as e:
            print(f"[RAG] Could not check database stats: {e}")

        return True
    except Exception as e:
        print(f"Warning: Could not initialize RAG database: {e}")
        return False

rag_available = load_rag_data()

# Streamlit configuration
st.set_page_config(
    page_title="MedAssistAI - Doctor Appointment Booking",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("MedAssistAI Chatbot")
st.markdown("### Book Your Doctor Appointment in Minutes")

# Initialize session state
if "sessions" not in st.session_state:
    st.session_state.sessions = {}
    st.session_state.sessions["default"] = SessionManager.create_session("Session 1")
    st.session_state.active_session_id = "default"

if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = "default"

# Get active session
active_session = st.session_state.sessions[st.session_state.active_session_id]

# Initialize booking state for current session (persists across messages)
if "booking_state" not in st.session_state:
    st.session_state.booking_state = {}

# Sidebar with session management
with st.sidebar:
    st.markdown("### Sessions")

    # New session button
    col1, col2 = st.columns([3, 1])
    with col1:
        new_session_name = st.text_input("Session name", placeholder="My Session", key="new_session_input")
    with col2:
        if st.button("+ New", use_container_width=True):
            if new_session_name.strip():
                new_session = SessionManager.create_session(new_session_name.strip())
                st.session_state.sessions[new_session.session_id] = new_session
                st.session_state.active_session_id = new_session.session_id
                # Clear booking state for new session
                st.session_state.booking_state = {}
                st.rerun()
            else:
                st.warning("Enter a session name")

    # Session selector
    st.divider()
    session_options = {sid: SessionManager.get_session_display_name(s) for sid, s in st.session_state.sessions.items()}

    selected_session = st.selectbox(
        "Switch session",
        options=list(session_options.keys()),
        format_func=lambda x: session_options[x],
        index=list(session_options.keys()).index(st.session_state.active_session_id),
        key="session_selector"
    )

    if selected_session != st.session_state.active_session_id:
        st.session_state.active_session_id = selected_session
        # Clear booking state when switching sessions to avoid context leakage
        st.session_state.booking_state = {}
        st.rerun()

    # Delete session button
    st.divider()
    if len(st.session_state.sessions) > 1:
        if st.button("[DEL] Delete Current Session", use_container_width=True):
            del st.session_state.sessions[st.session_state.active_session_id]
            st.session_state.active_session_id = list(st.session_state.sessions.keys())[0]
            st.rerun()

    st.divider()

    st.markdown("### RAG System")
    if rag_available:
        st.caption("[OK] Vector database loaded - using doctor & patient context")
        try:
            rag_db = initialize_rag_db()
            stats = rag_db.get_db_stats()
            if stats:
                st.caption(f"Chunks indexed: {stats.get('total_chunks', 0)}")
        except:
            pass
    else:
        st.caption("[WARN] Vector database not available")

    st.divider()

    st.markdown("### LangSmith Integration")
    st.caption("All conversations are traced for debugging")

    langsmith_url = get_langsmith_project_url()
    if st.button("[LINK] Open LangSmith Studio", use_container_width=True):
        st.write(f"[Open LangSmith Studio]({langsmith_url})")

    with st.expander("[INFO] LangSmith Info", expanded=False):
        st.markdown(f"**Project:** `{os.getenv('LANGSMITH_PROJECT', 'medassistai-chatbot')}`")
        st.markdown(f"**Endpoint:** `{os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')}`")
        st.markdown(f"**Tracing:** Enabled [OK]")

# Main chat interface
st.subheader(f"Conversation - {active_session.name}")
chat_container = st.container(height=400, border=True)

for message in active_session.chat_history:
    with chat_container.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Type your message here... (e.g., 'I want to book an appointment with Dr. Willi Bedna')")

if user_input:
    # Add user message to chat
    active_session.chat_history.append({
        "role": "user",
        "content": user_input
    })

    # Update conversation history for context
    active_session.conversation_history.append({
        "role": "user",
        "content": user_input
    })

    # Create chat state, restore from session if available
    chat_state = ChatState(
        messages=active_session.chat_history,
        user_input=user_input,
        conversation_history=active_session.conversation_history,
        available_doctors=list(DOCTOR_PROFILES.keys()),
        patient_id=st.session_state.booking_state.get("patient_id"),
        extracted_info=st.session_state.booking_state.get("extracted_info", {}),
        use_rag_context=st.session_state.booking_state.get("use_rag_context", False),
        requested_specialization=st.session_state.booking_state.get("requested_specialization"),
        has_available_doctor=st.session_state.booking_state.get("has_available_doctor", False),
        appointment_ready_for_confirmation=st.session_state.booking_state.get("appointment_ready_for_confirmation", False),
        is_deceased_patient=st.session_state.booking_state.get("is_deceased_patient", False),
        patient_not_found=st.session_state.booking_state.get("patient_not_found", False),
        should_add_patient=st.session_state.booking_state.get("should_add_patient", False),
    )

    # Process through LangGraph
    with st.spinner("Processing your request..."):
        try:
            # DEBUG: Show input state
            with st.expander("[DEBUG] Input State"):
                st.write(f"**Intent:** {chat_state.detected_intent}")
                st.write(f"**Patient ID:** {chat_state.patient_id}")
                st.write(f"**Confirmation Ready:** {chat_state.appointment_ready_for_confirmation}")
                st.write(f"**Extracted Info:** {chat_state.extracted_info}")

            # Invoke the graph with the current state
            result = graph.invoke(chat_state)

            # DEBUG: Show result state
            with st.expander("[DEBUG] Result State"):
                st.write(f"**Booking Confirmed:** {result.get('booking_confirmed', False)}")
                st.write(f"**Patient ID:** {result.get('patient_id')}")
                st.write(f"**Appointment Ready:** {result.get('appointment_ready_for_confirmation', False)}")
                st.write(f"**Extracted Info:** {result.get('extracted_info', {})}")
                st.write(f"**Intent:** {result.get('detected_intent')}")

            # Extract the response
            assistant_response = result.get("last_response", "I apologize, I couldn't process your request. Please try again.")

            # Ensure response is a string
            if isinstance(assistant_response, dict):
                assistant_response = assistant_response.get('text', str(assistant_response))
            elif isinstance(assistant_response, list):
                assistant_response = assistant_response[0] if assistant_response else "No response"
            else:
                assistant_response = str(assistant_response)

            # Add assistant message to chat
            active_session.chat_history.append({
                "role": "assistant",
                "content": assistant_response
            })

            active_session.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })

            # Save booking state for next message
            st.session_state.booking_state = {
                "patient_id": result.get("patient_id"),
                "extracted_info": result.get("extracted_info", {}),
                "use_rag_context": result.get("use_rag_context", False),
                "requested_specialization": result.get("requested_specialization"),
                "has_available_doctor": result.get("has_available_doctor", False),
                "appointment_ready_for_confirmation": result.get("appointment_ready_for_confirmation", False),
                "is_deceased_patient": result.get("is_deceased_patient", False),
                "patient_not_found": result.get("patient_not_found", False),
                "should_add_patient": result.get("should_add_patient", False),
            }

            # DEBUG: Show saved state
            with st.expander("[DEBUG] Saved Booking State"):
                st.json(st.session_state.booking_state)

            # Log successful execution to LangSmith
            detected_intent = result.get("detected_intent", Intent.UNKNOWN).value if result.get("detected_intent") else "unknown"
            log_agent_run(
                session_id=st.session_state.active_session_id,
                intent=detected_intent,
                success=True
            )

            # Display booking status if applicable
            if result.get("booking_confirmed"):
                st.success("Appointment booking confirmed!")
                with st.expander("Booking Details"):
                    booking_details = {
                        "doctor": result.get("extracted_info", {}).get("doctor_name"),
                        "date": result.get("extracted_info", {}).get("appointment_date"),
                        "time": result.get("extracted_info", {}).get("appointment_time"),
                        "reason": result.get("extracted_info", {}).get("reason"),
                    }
                    st.json(booking_details)
                    st.info(f"Trello Card should have been created with: Date={booking_details['date']}, Time={booking_details['time']}")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            st.error(error_msg)
            active_session.chat_history.append({
                "role": "assistant",
                "content": error_msg
            })

            # Log error to LangSmith
            log_agent_run(
                session_id=st.session_state.active_session_id,
                intent="unknown",
                success=False,
                error=str(e)
            )

    # Rerun to update the chat display
    st.rerun()

# Footer with debugging info
with st.expander("[DEBUG] Information"):
    col_debug1, col_debug2 = st.columns(2)
    with col_debug1:
        st.subheader("LangSmith Project")
        st.code(os.getenv("LANGSMITH_PROJECT", "medassistai-chatbot"))
    with col_debug2:
        st.subheader("Conversation Messages")
        st.code(f"Total: {len(active_session.conversation_history)}")
    col_debug3, col_debug4 = st.columns(2)
    with col_debug3:
        st.subheader("Active Session")
        st.code(st.session_state.active_session_id)
    with col_debug4:
        st.subheader("Total Sessions")
        st.code(f"{len(st.session_state.sessions)}")

    st.divider()
    st.subheader("Chat State")
    st.json({
        "session_id": st.session_state.active_session_id,
        "messages_count": len(active_session.chat_history),
        "conversation_history": len(active_session.conversation_history),
    })

