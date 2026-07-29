"""Parse natural language dates and times using LLM."""
import json
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from intent_detector import _extract_text


DATE_TIME_PARSER_PROMPT = ChatPromptTemplate.from_template("""
Convert natural language date and time expressions to strict ISO format.

Current date/time: {current_datetime}

User input: {user_input}

Extract and convert the following to JSON (use null if not mentioned):
- appointment_date: ISO date format (YYYY-MM-DD)
- appointment_time: 24-hour format (HH:MM)

Examples:
- "tomorrow at 2:30 PM" → {{"appointment_date": "2026-07-30", "appointment_time": "14:30"}}
- "next Monday 9 AM" → {{"appointment_date": "2026-07-28", "appointment_time": "09:00"}}
- "in 3 days" → {{"appointment_date": "2026-08-01", "appointment_time": null}}
- "12:34 PM" → {{"appointment_date": null, "appointment_time": "12:34"}}

Return ONLY valid JSON, no additional text.
""")


def parse_date_time(user_input: str) -> dict:
    """Parse natural language date and time to strict format.

    Returns:
        dict with 'appointment_date' (YYYY-MM-DD) and 'appointment_time' (HH:MM)
    """
    if not user_input:
        return {"appointment_date": None, "appointment_time": None}

    try:
        llm = get_llm()
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        chain = DATE_TIME_PARSER_PROMPT | llm
        response = chain.invoke({
            "current_datetime": current_datetime,
            "user_input": user_input
        })

        content = _extract_text(response)

        # Try to extract JSON from the response
        # LLM might wrap JSON in markdown or add extra text
        import re
        json_match = re.search(r'\{[^}]*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        # Parse JSON response
        parsed = json.loads(content)

        # Validate and clean the response
        result = {
            "appointment_date": None,
            "appointment_time": None
        }

        if parsed.get("appointment_date"):
            date_str = parsed["appointment_date"]
            # Validate format YYYY-MM-DD
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                result["appointment_date"] = date_str
            except ValueError:
                pass

        if parsed.get("appointment_time"):
            time_str = parsed["appointment_time"]
            # Validate format HH:MM
            try:
                datetime.strptime(time_str, "%H:%M")
                result["appointment_time"] = time_str
            except ValueError:
                pass

        return result

    except json.JSONDecodeError as e:
        return {"appointment_date": None, "appointment_time": None}
    except Exception as e:
        return {"appointment_date": None, "appointment_time": None}


def format_appointment_date_time(date_str: str, time_str: str) -> str:
    """Format appointment date and time for display.

    Args:
        date_str: YYYY-MM-DD format
        time_str: HH:MM format

    Returns:
        Human-readable format like "July 30, 2026 at 2:34 PM"
    """
    try:
        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%B %d, %Y")

            if time_str:
                time_obj = datetime.strptime(time_str, "%H:%M")
                time_formatted = time_obj.strftime("%I:%M %p")
                return f"{date_formatted} at {time_formatted}"
            return date_formatted

        elif time_str:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.strftime("%I:%M %p")

        return "Not specified"

    except Exception as e:
        print(f"[WARN] Error formatting date/time: {e}")
        return f"{date_str or 'N/A'} {time_str or 'N/A'}"
