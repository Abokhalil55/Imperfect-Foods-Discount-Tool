from openai import OpenAI
import json
import os
import re
import requests

from dotenv import load_dotenv
from database import get_available_inventory, supabase
from notifications import send_interest_confirmation_email

load_dotenv(override=True)

openAI_API_key = os.getenv("gpt_API_KEY")
gpt = OpenAI(base_url="https://api.openai.com/v1", api_key=openAI_API_key)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

LOCATIONS = ["Cyberjaya", "Petaling Jaya", "Putrajaya", "Puchong"]
CATEGORIES = [
    "Produce",
    "Bakery & Grains",
    "Dairy & Chilled Items",
    "Prepared / Packaged Meals",
]


def push(text):
    """Send an internal Pushover note without breaking customer support if it fails."""
    if not pushover_user or not pushover_token:
        return False
    try:
        response = requests.post(
            pushover_url,
            data={"user": pushover_user, "token": pushover_token, "message": text},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as error:
        print(f"Pushover failed: {error}")
        return False


def normalize_location(value):
    raw = (value or "").strip().lower()
    for location in LOCATIONS:
        if location.lower() == raw:
            return location
    return None


def normalize_category(value):
    raw = (value or "").strip().lower()
    for category in CATEGORIES:
        if category.lower() == raw:
            return category
    return None


def infer_category(item_query):
    text = (item_query or "").lower()
    keyword_groups = {
        "Produce": ["produce", "fruit", "vegetable", "carrot", "banana", "apple", "tomato", "spinach", "pear", "orange", "mango", "potato"],
        "Bakery & Grains": ["bakery", "grain", "bread", "croissant", "muffin", "bagel", "sourdough", "roll", "bun", "cake"],
        "Dairy & Chilled Items": ["dairy", "milk", "yogurt", "cheese", "butter", "mozzarella", "chilled"],
        "Prepared / Packaged Meals": ["prepared", "packaged", "meal", "rice", "nasi", "sandwich", "pasta", "mee", "wrap", "salad"],
    }
    for category, keywords in keyword_groups.items():
        if any(keyword in text for keyword in keywords):
            return category
    return None


def check_inventory_availability(item_query, location):
    """Check live Supabase inventory for a requested item/category in one supported location."""
    location = normalize_location(location)
    if not location:
        return {"available": False, "error": "Unsupported location.", "supported_locations": LOCATIONS}

    query = (item_query or "").strip().lower()
    if not query:
        return {"available": False, "error": "No item was provided."}

    query_tokens = [token for token in re.findall(r"[a-z0-9]+", query) if len(token) > 2]
    matches = []

    for item in get_available_inventory(location):
        name = str(item.get("name", ""))
        category = str(item.get("category", ""))
        haystack = f"{name} {category}".lower()

        matched = query in haystack
        if not matched and query_tokens:
            matched = all(token in haystack for token in query_tokens)

        if matched:
            store = item.get("stores") or {}
            if isinstance(store, list):
                store = store[0] if store else {}
            matches.append({
                "name": name,
                "category": category,
                "store": store.get("name", "Unknown store"),
                "location": item.get("location"),
                "quantity": float(item.get("quantity") or 0),
                "price_myr": float(item.get("new_price") or 0),
                "days_left": item.get("days_left"),
            })

    return {
        "available": bool(matches),
        "query": item_query,
        "location": location,
        "matches": matches[:6],
        "suggested_category": infer_category(item_query),
    }


def record_user_details(email, spot, interested_in):
    """Save one notification interest idempotently and send an immediate confirmation email."""
    email = (email or "").strip().lower()
    location = normalize_location(spot)
    category = normalize_category(interested_in)

    if "@" not in email or "." not in email.split("@")[-1]:
        return {"status": "invalid", "message": "A valid email address is required."}
    if not location:
        return {"status": "invalid", "message": "Choose Cyberjaya, Petaling Jaya, Putrajaya, or Puchong."}
    if not category:
        return {"status": "invalid", "message": "Choose one supported food category."}

    existing = (
        supabase.table("notifications")
        .select("id")
        .eq("email", email)
        .eq("location", location)
        .eq("interested_in", category)
        .limit(1)
        .execute()
    )

    if existing.data:
        return {
            "status": "already_saved",
            "message": "This exact interest is already saved. Do not save it again.",
        }

    try:
        supabase.table("notifications").insert({
            "email": email,
            "location": location,
            "interested_in": category,
        }).execute()
    except Exception as error:
        if "23505" in str(error) or "duplicate key" in str(error).lower():
            return {
                "status": "already_saved",
                "message": "This exact interest is already saved. Do not save it again.",
            }
        raise

    email_sent = False
    try:
        send_interest_confirmation_email(email, location, category)
        email_sent = True
    except Exception as error:
        print(f"Interest confirmation email failed for {email}: {error}")

    push(f"Interest recorded: {email} | {location} | {category}")

    return {
        "status": "saved",
        "email_confirmation": "sent" if email_sent else "failed",
        "message": "Interest saved successfully.",
    }


def record_unknown_question(question, email="Not provided"):
    push(f"User {email} asked a question I could not answer: {question}")
    return {"status": "recorded"}


def customer_complaint(email, location, store_name, complaint):
    push(f"Complaint from {email} about {store_name} in {location}: {complaint}")
    return {"status": "recorded"}


system_prompt = """
You are JimatRasa Customer Support for a Malaysian surplus-food marketplace.
Be concise, practical and accurate. All prices are Malaysian Ringgit (MYR/RM).

Supported locations: Cyberjaya, Petaling Jaya, Putrajaya, Puchong.
Supported categories: Produce; Bakery & Grains; Dairy & Chilled Items; Prepared / Packaged Meals.

IMPORTANT LIVE INVENTORY RULES
- When a customer asks whether an item or category is available in a specific supported location, you MUST call `check_inventory_availability` before answering.
- Never guess live availability and never use `record_unknown_question` for an availability question.
- If the tool says available=true, clearly say it is available right now and summarize the matching item(s), seller, price, stock and days left when useful.
- If the tool says available=false, clearly say it is not available right now in that location. Then ask for the customer's email so you can note their interest and notify them when a matching item is newly listed.
- For an unavailable item, use the tool's suggested_category when it is present. If the category is genuinely ambiguous, ask the customer which one of the four supported categories it belongs to.

INTEREST / EMAIL FOLLOW-UP
- Call `record_user_details` only after you have email, location and one supported category.
- If the tool returns status=saved, tell the customer the interest is saved. If email_confirmation=sent, mention that a confirmation email was sent and that future matching listings will trigger an alert.
- If email_confirmation=failed, say the interest was saved but the confirmation email could not be sent right now. Do not expose technical SMTP details.
- If the tool returns status=already_saved, simply say the alert is already saved. Do NOT call the tool again.
- If a customer says "ok", "okay", "alright", "thanks", or similar after an interest was already saved, respond normally and DO NOT call `record_user_details` again.

PRICING
Dynamic discounts use days left plus cosmetic grade. Days left contributes 45% for 1 day, 30% for 2-3 days, and 15% for 4-7 days. Grade contributes A=5%, B=15%, C=25%. Total discount is capped at 80%.

QUALITY / STORAGE
Items are evaluated before listing. Give normal storage advice when asked: produce away from ethylene producers where relevant, bakery can be frozen, dairy at or below 4°C, prepared food should follow safe refrigeration/resealing guidance.

COMPLAINTS
Use `customer_complaint` only when the customer supplies email, store name, supported location, and complaint details.

UNKNOWN QUESTIONS
Use `record_unknown_question` only when the question cannot be answered from the system rules or available tools. Do not fabricate data.

Do not process purchases or modify stock from support chat. Direct customers to the Market for purchases.
"""


check_inventory_json = {
    "name": "check_inventory_availability",
    "description": "Check live JimatRasa inventory for a specific item or food category in a supported location. Always use this for availability questions.",
    "parameters": {
        "type": "object",
        "properties": {
            "item_query": {"type": "string", "description": "The specific food item or category the customer is asking about, such as bread, milk, bananas, or Bakery & Grains."},
            "location": {"type": "string", "enum": LOCATIONS},
        },
        "required": ["item_query", "location"],
        "additionalProperties": False,
    },
}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Save a customer's email interest for one food category in one location so they can receive stock alerts.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "spot": {"type": "string", "enum": LOCATIONS},
            "interested_in": {"type": "string", "enum": CATEGORIES},
        },
        "required": ["email", "spot", "interested_in"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Record a JimatRasa question that cannot be answered using the known rules or available tools.",
    "parameters": {
        "type": "object",
        "properties": {"question": {"type": "string"}},
        "required": ["question"],
        "additionalProperties": False,
    },
}

customer_complaint_json = {
    "name": "customer_complaint",
    "description": "Record a customer's complaint about a specific JimatRasa seller/store.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "store_name": {"type": "string"},
            "location": {"type": "string", "enum": LOCATIONS},
            "complaint": {"type": "string"},
        },
        "required": ["email", "store_name", "location", "complaint"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": check_inventory_json},
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
    {"type": "function", "function": customer_complaint_json},
]

tool_map = {
    "check_inventory_availability": check_inventory_availability,
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
    "customer_complaint": customer_complaint,
}


def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        try:
            arguments = json.loads(tool_call.function.arguments)
            tool_used = tool_map.get(tool_call.function.name)
            result = tool_used(**arguments) if tool_used else {"error": "Tool not found"}
        except Exception as error:
            print(f"Support tool failed ({tool_call.function.name}): {error}")
            result = {"error": "The support action could not be completed right now."}

        results.append({
            "role": "tool",
            "content": json.dumps(result, default=str),
            "tool_call_id": tool_call.id,
        })
    return results


def chat(message, history):
    clean_history = [
        {"role": h["role"], "content": h["content"]}
        for h in history
        if h.get("role") in {"user", "assistant"} and h.get("content")
    ]
    messages = [{"role": "system", "content": system_prompt}] + clean_history + [{"role": "user", "content": message}]

    for _ in range(5):
        response = gpt.chat.completions.create(
            model="gpt-5.4-nano",
            messages=messages,
            tools=tools,
        )
        assistant_message = response.choices[0].message

        if response.choices[0].finish_reason != "tool_calls":
            return assistant_message.content or "How can I help with JimatRasa?"

        messages.append(assistant_message)
        messages.extend(handle_tool_calls(assistant_message.tool_calls))

    return "I could not complete that support request. Please try again."


def run_customer_service():
    """Interactive customer service chat session."""
    print("\n--- [ JimatRasa Customer Service ] ---")
    history = []
    print("\nAsk about stock, discounts, storage, or follow-up. Type 'back' to return to the main menu.\n")

    while True:
        message = input("You: ").strip()
        if not message:
            continue
        if message.lower() in ("back", "exit", "quit"):
            print("\nReturning to main menu...")
            break

        reply = chat(message, history)
        print(f"\nJimatRasa Support: {reply}\n")
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
