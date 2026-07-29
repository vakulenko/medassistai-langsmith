import streamlit as st
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent, SessionManager, Session
from config import DOCTOR_PROFILES

# Load environment variables
load_dotenv()

# Configure LangSmith for tracing
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT")
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "medassistai-chatbot"

# Streamlit configuration
st.set_page_config(
    page_title="MedAssistAI - Doctor Appointment Booking",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 MedAssistAI Chatbot")
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

# Sidebar with session management
with st.sidebar:
    st.markdown("### 📋 Sessions")

    # New session button
    col1, col2 = st.columns([3, 1])
    with col1:
        new_session_name = st.text_input("Session name", placeholder="My Session", key="new_session_input")
    with col2:
        if st.button("➕ New", use_container_width=True):
            if new_session_name.strip():
                new_session = SessionManager.create_session(new_session_name.strip())
                st.session_state.sessions[new_session.session_id] = new_session
                st.session_state.active_session_id = new_session.session_id
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
        st.rerun()

    # Delete session button
    st.divider()
    if len(st.session_state.sessions) > 1:
        if st.button("🗑️ Delete Current Session", use_container_width=True):
            del st.session_state.sessions[st.session_state.active_session_id]
            st.session_state.active_session_id = list(st.session_state.sessions.keys())[0]
            st.rerun()

    st.divider()
    st.caption("🔍 LangSmith Tracing Enabled - All conversations are tracked for quality assurance")

# Main chat interface
st.subheader(f"💬 Conversation - {active_session.name}")
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

    # Create chat state
    chat_state = ChatState(
        messages=active_session.chat_history,
        user_input=user_input,
        conversation_history=active_session.conversation_history,
        available_doctors=list(DOCTOR_PROFILES.keys())
    )

    # Process through LangGraph
    with st.spinner("Processing your request..."):
        try:
            # Invoke the graph with the current state
            result = graph.invoke(chat_state)

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

            # Display booking status if applicable
            if result.get("booking_confirmed"):
                st.success("✅ Appointment booking confirmed!")
                with st.expander("📅 Booking Details"):
                    st.json({
                        "doctor": result.get("extracted_info", {}).get("doctor_name"),
                        "date": result.get("extracted_info", {}).get("appointment_date"),
                        "time": result.get("extracted_info", {}).get("appointment_time"),
                        "reason": result.get("extracted_info", {}).get("reason"),
                    })

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            st.error(error_msg)
            active_session.chat_history.append({
                "role": "assistant",
                "content": error_msg
            })

    # Rerun to update the chat display
    st.rerun()

# Footer with debugging info
with st.expander("🔧 Debug Information"):
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

