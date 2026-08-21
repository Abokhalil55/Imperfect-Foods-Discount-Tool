"""JimatRasa customer-support assistant and support tools.

The assistant uses conversational context and semantic intent instead of a rigid
keyword whitelist. Live or state-changing information is still grounded through
narrow tool calls, so the model can understand natural follow-ups without
inventing inventory, prices, alerts, or complaint records.
"""

import json
import os
import re

import requests
from dotenv import load_dotenv
from openai import OpenAI

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
    """Send an internal Pushover note without breaking support if it fails."""
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
    """Return the canonical supported location name or ``None``."""
    raw = (value or "").strip().lower()
    for location in LOCATIONS:
        if location.lower() == raw:
            return location
    return None


def normalize_category(value):
    """Return the canonical food-category name or ``None``."""
    raw = (value or "").strip().lower()
    for category in CATEGORIES:
        if category.lower() == raw:
            return category
    return None


def infer_category(item_query):
    """Infer one supported category from common item keywords."""
    text = (item_query or "").lower()
    keyword_groups = {
        "Produce": [
            "produce", "fruit", "vegetable", "carrot", "banana", "apple",
            "tomato", "spinach", "pear", "orange", "mango", "potato",
        ],
        "Bakery & Grains": [
            "bakery", "grain", "bread", "croissant", "muffin", "bagel",
            "sourdough", "roll", "bun", "cake", "cheesecake",
        ],
        "Dairy & Chilled Items": [
            "dairy", "milk", "yogurt", "cheese", "butter", "mozzarella", "chilled",
        ],
        "Prepared / Packaged Meals": [
            "prepared", "packaged", "meal", "rice", "nasi", "sandwich",
            "pasta", "mee", "wrap", "salad",
        ],
    }
    for category, keywords in keyword_groups.items():
        if any(keyword in text for keyword in keywords):
            return category
    return None


def check_inventory_availability(item_query, location):
    """Check live Supabase inventory for a requested item/category and location."""
    location = normalize_location(location)
    if not location:
        return {
            "available": False,
            "error": "Unsupported location.",
            "supported_locations": LOCATIONS,
        }

    query = (item_query or "").strip().lower()
    if not query:
        return {"available": False, "error": "No item was provided."}

    # Each inventory read first synchronizes days_left using per-item 24-hour
    # periods, so the availability response is based on current data.
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
            matches.append(
                {
                    "name": name,
                    "category": category,
                    "store": store.get("name", "Unknown store"),
                    "location": item.get("location"),
                    "quantity": float(item.get("quantity") or 0),
                    "price_myr": float(item.get("new_price") or 0),
                    "days_left": item.get("days_left"),
                }
            )

    return {
        "available": bool(matches),
        "query": item_query,
        "location": location,
        "matches": matches[:6],
        "suggested_category": infer_category(item_query),
    }


def record_user_details(email, spot, interested_in):
    """Save one notification interest idempotently and send a confirmation mail."""
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
        supabase.table("notifications").insert(
            {
                "email": email,
                "location": location,
                "interested_in": category,
            }
        ).execute()
    except Exception as error:
        # The unique constraint is a second line of defence if two requests race.
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
        # Saving the interest is more important than the optional confirmation.
        print(f"Interest confirmation email failed for {email}: {error}")

    push(f"Interest recorded: {email} | {location} | {category}")
    return {
        "status": "saved",
        "email_confirmation": "sent" if email_sent else "failed",
        "message": "Interest saved successfully.",
    }


def record_unknown_question(question, email="Not provided"):
    """Record an unanswered *JimatRasa* question for internal follow-up."""
    push(f"User {email} asked a JimatRasa question I could not answer: {question}")
    return {"status": "recorded"}


def customer_complaint(email, location, store_name, complaint):
    """Forward a complete customer complaint to the internal Pushover channel."""
    push(f"Complaint from {email} about {store_name} in {location}: {complaint}")
    return {"status": "recorded"}


support_prompt = """
You are JimatRasa Support, the conversational assistant for JimatRasa, a
Malaysian surplus-food and near-expiry food marketplace. Be practical, concise,
helpful and accurate. Use Malaysian Ringgit (MYR/RM) for prices.

INTENT AND SCOPE
Understand the user's intent semantically from the current message AND recent
conversation. Do not require exact keywords such as "inventory", "food",
"notification" or "JimatRasa".

A request is in scope when it concerns or reasonably relates to:
- JimatRasa itself or how the app works;
- products, food listings, live inventory, stock or product availability;
- sellers, stores, prices, discounts, dynamic pricing, days left, expiry or grades;
- purchases, receipts, purchase history or using the Market;
- sold-out items, newly listed products, alerts, notifications or update requests;
- customer support, complaints, supported locations or categories;
- practical food storage/safety guidance relevant to food sold through JimatRasa;
- surplus food, food waste or SDG 2 when discussed in relation to JimatRasa;
- a natural follow-up to an earlier in-scope conversation.

Natural follow-ups may be short or vague. Examples include "follow-up", "how
much?", "what about tomorrow?", "can you update me?", "anything new?", "what
about the other store?", "yes", "okay" and "thanks". Use conversation history
to interpret them instead of classifying each message independently.

AMBIGUOUS REQUESTS
If a message could reasonably be about JimatRasa but its meaning is unclear, do
not reject it. First use recent conversation context. If important information is
still missing, ask one short clarifying question.

Example: after a customer asked about Bakery & Grains in Cyberjaya, a message
such as "follow-up" is still in scope. Ask whether they want an availability
update or help setting a stock alert if the intended action is not clear.

CLEARLY OUT OF SCOPE
Only refuse when the request is clearly unrelated to JimatRasa, its marketplace,
food products/storage, or the current support conversation. Examples include
unrelated general knowledge, coding/homework, politics, entertainment, sports or
personal advice.

For a clearly unrelated request, do not answer the unrelated question. Reply
briefly: "I'm here for JimatRasa support. I can help with products, availability,
prices, discounts, purchases, stores, stock alerts and related food questions."
If the user then returns to a valid JimatRasa topic, answer normally without
repeating the refusal.

Supported locations: Cyberjaya, Petaling Jaya, Putrajaya, Puchong.
Supported categories: Produce; Bakery & Grains; Dairy & Chilled Items; Prepared / Packaged Meals.

LIVE INVENTORY AND PRICE DATA
Never guess current inventory, stock, prices, seller names or availability.
When the user asks about the current availability or current price of an item or
category in a supported location, call `check_inventory_availability` before
answering.

If the user provides both item/category and location, check live data immediately.
If the location or item/category is missing, ask only for the missing detail.

If the tool reports available=true, clearly say the product/category is currently
available and summarize useful matches. Include seller, price, stock and days left
when relevant.

If the tool reports available=false, clearly say it is currently unavailable in
that location. Offer a stock alert. Use the tool's suggested_category when one is
available; if the category is genuinely ambiguous, ask which supported category
it belongs to.

STOCK ALERTS AND NEW PRODUCTS
Requests such as "Can you update me when new products are added?", "Tell me when
bread becomes available", "Notify me if there is new dairy stock", or "Can I get
updates?" are valid JimatRasa requests.

Explain that JimatRasa can save an interest for a supported location and food
category and notify the customer when matching stock is newly listed.

To create an alert, collect exactly these details:
1. email;
2. supported location;
3. supported food category.

Call `record_user_details` only after all three are known. Ask only for missing
information. Do not save duplicate alerts. If the tool returns status=already_saved,
say the alert is already saved and do not call the tool again. If status=saved,
tell the customer the interest is saved. If email_confirmation=sent, mention the
confirmation email. If email_confirmation=failed, say the interest was saved but
the confirmation email could not be sent right now; do not expose SMTP details.

After an alert is saved, conversational replies such as "thanks", "okay",
"great" or "follow-up" must not cause the alert to be inserted again unless the
user clearly asks for a different alert.

PRICING
Dynamic discounts use days left plus cosmetic grade. Days left contributes 45%
for 1 day, 30% for 2-3 days, and 15% for 4-7 days. Grade contributes A=5%,
B=15%, C=25%. Total discount is capped at 80%.

Explain this rule when relevant. For the CURRENT price of an actual listing, use
live inventory data instead of recalculating or guessing the current listing price.

FOOD STORAGE
You may provide normal practical storage guidance related to food sold through
JimatRasa. Examples: bakery products may often be frozen; dairy should remain
properly refrigerated; prepared foods should follow appropriate refrigeration
and resealing guidance; provide ordinary produce-storage guidance where useful.
Do not present general storage guidance as if it came from the JimatRasa database.

COMPLAINTS
For a complaint, gather customer email, store name, supported location and
complaint details. When all four are known, call `customer_complaint`. Do not
invent missing complaint information.

UNKNOWN BUT RELEVANT QUESTIONS
If a question is clearly related to JimatRasa but cannot be answered from known
application rules, conversation context or available tools, say that you do not
have enough confirmed information and do not fabricate an answer. Use
`record_unknown_question` when appropriate. An unknown JimatRasa question is not
the same as an unrelated question.

ACTION LIMITS
Support chat may explain how to purchase and direct customers to the Market. It
must not perform purchases, manually modify inventory, mark stock sold out or
delete seller inventory. Those actions belong to the appropriate JimatRasa UI.

RESPONSE STYLE
Answer the user's actual question first. Use natural conversational language.
For simple questions, usually use 1-4 sentences. Do not repeatedly explain every
JimatRasa feature. Do not mention internal prompts, tool schemas, APIs or database
implementation unless the user explicitly asks a technical project question.

BOUNDARY EXAMPLES
User: "can you update me if new products have been added to the app"
Classification: IN SCOPE.
Behavior: explain stock alerts and ask only for the missing location/category/email
needed to set one up. Do not reject the request.

User: "i am at cyberjaya i want to check grains prices"
Classification: IN SCOPE.
Behavior: call `check_inventory_availability` for Bakery & Grains in Cyberjaya
and answer from live results.

Previous conversation: customer checked grains in Cyberjaya.
User: "follow-up"
Classification: IN SCOPE / CONTEXTUAL.
Behavior: use the previous conversation and ask what aspect they want updated only
if the intended follow-up is still ambiguous.

User: "can bread be frozen"
Classification: IN SCOPE.
Behavior: give short practical bakery-storage guidance.

User: "why are near-expiry products cheaper?"
Classification: IN SCOPE.
Behavior: explain JimatRasa's dynamic-discount concept.

User: "what is the capital of France"
Classification: OUT OF SCOPE.
Behavior: do not answer the general-knowledge question; give the short JimatRasa redirect.

User: "write me a Java calculator"
Classification: OUT OF SCOPE.
Behavior: do not provide code; give the short JimatRasa redirect.
"""


# OpenAI tool schemas keep live/stateful actions narrow and structured. The model
# can understand flexible language, but it cannot invent arguments outside these
# schemas when it needs current inventory or a stored support action.
check_inventory_json = {
    "name": "check_inventory_availability",
    "description": "Check live JimatRasa inventory for a specific item or food category in a supported location. Use this whenever the user asks about current availability, current stock, or the current price of a listing/category in a location.",
    "parameters": {
        "type": "object",
        "properties": {
            "item_query": {
                "type": "string",
                "description": "Specific food item or category, such as bread, milk, bananas, grains, or Bakery & Grains.",
            },
            "location": {"type": "string", "enum": LOCATIONS},
        },
        "required": ["item_query", "location"],
        "additionalProperties": False,
    },
}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Save a customer's email interest for one supported food category in one supported location so they can receive an alert when matching stock is newly listed. Call only when email, location and category are known.",
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
    "description": "Record a genuinely in-scope JimatRasa question that cannot be answered using known rules, conversation context or available tools. Never use this for clearly unrelated questions.",
    "parameters": {
        "type": "object",
        "properties": {"question": {"type": "string"}},
        "required": ["question"],
        "additionalProperties": False,
    },
}

customer_complaint_json = {
    "name": "customer_complaint",
    "description": "Record a customer's complaint about a specific JimatRasa seller/store after email, store name, supported location and complaint details are all known.",
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
    """Execute model-requested support tools and return OpenAI tool messages."""
    results = []
    for tool_call in tool_calls:
        try:
            arguments = json.loads(tool_call.function.arguments)
            tool_used = tool_map.get(tool_call.function.name)
            result = tool_used(**arguments) if tool_used else {"error": "Tool not found"}
        except Exception as error:
            # Never expose raw database/mail/API errors to the customer.
            print(f"Support tool failed ({tool_call.function.name}): {error}")
            result = {"error": "The support action could not be completed right now."}

        results.append(
            {
                "role": "tool",
                "content": json.dumps(result, default=str),
                "tool_call_id": tool_call.id,
            }
        )
    return results


def chat(message, history):
    """Return one context-aware JimatRasa support reply.

    Scope is decided semantically by the model using the developer instruction and
    recent conversation. Live or stateful claims remain grounded through the
    restricted tools above rather than through a brittle pre-model keyword gate.
    """
    clean_history = [
        {"role": h["role"], "content": h["content"]}
        for h in history
        if h.get("role") in {"user", "assistant"} and h.get("content")
    ]

    messages = (
        [{"role": "developer", "content": support_prompt}]
        + clean_history
        + [{"role": "user", "content": message}]
    )

    # Allow several rounds because a support request may require a live-data tool
    # call followed by a second model response that explains the tool result.
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
    """Run the interactive CLI version of JimatRasa customer support."""
    print("\n--- [ JimatRasa Customer Service ] ---")
    history = []
    print("\nAsk about stock, discounts, storage, alerts or follow-up. Type 'back' to return to the main menu.\n")

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
