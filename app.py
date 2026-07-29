import streamlit as st
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent
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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Sidebar with info
with st.sidebar:
    st.caption("🔍 LangSmith Tracing Enabled - All conversations are tracked for quality assurance")

# Main chat interface
st.subheader("💬 Conversation")
chat_container = st.container(height=400, border=True)

for message in st.session_state.chat_history:
    with chat_container.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Type your message here... (e.g., 'I want to book an appointment with Dr. Willi Bedna')")

if user_input:
    # Add user message to chat
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    # Update conversation history for context
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_input
    })

    # Create chat state
    chat_state = ChatState(
        messages=st.session_state.chat_history,
        user_input=user_input,
        conversation_history=st.session_state.conversation_history,
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
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": assistant_response
            })

            st.session_state.conversation_history.append({
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
            st.session_state.chat_history.append({
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
        st.code(f"Total: {len(st.session_state.conversation_history)}")

