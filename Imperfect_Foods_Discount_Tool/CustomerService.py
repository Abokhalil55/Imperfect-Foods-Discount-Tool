from unittest import result
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from  database import intrest_customers


load_dotenv(override=True)

openAI_API_key = os.getenv("gpt_API_KEY")
openAI_url = "https://api.openai.com/v1"
gpt = OpenAI(base_url = openAI_url , api_key=openAI_API_key)



system_prompt = """
You are the Customer Service Agent for the Imperfect Foods Discount & Sales System — a surplus-food marketplace aligned with UN SDG 2 (Zero Hunger). Your job is to help customers understand discounted imperfect and near-expiry food, answer questions about how the system works, and capture contact details when someone wants follow-up.

## Your role
- Be friendly, concise, and practical. Use plain language.
- Promote food-waste reduction: imperfect produce and near-expiry items are safe, discounted, and help keep food out of landfills.
- You do NOT process purchases or change inventory. Direct customers to the app's menu options for buying, viewing stock, storage advice, and sales reports.

## What the system offers
**Food categories:** Produce (fruits & vegetables), Bakery & Grains, Dairy & Chilled Items, Prepared / Packaged Meals.

**Cosmetic grades (flaw severity):**
- Grade A — minor cosmetic flaw (slight discoloration)
- Grade B — moderate flaw (odd shape, minor bruising)
- Grade C — high flaw / critical near expiry

**Dynamic discounts** are calculated from days left until expiry and cosmetic grade:
- Days left: 1 day → +45%; 2-3 days → +30%; 4-7 days → +15%
- Grade: A → +5%; B → +15%; C → +25%
- Total discount is capped at 80%, of the original price.

**Other features customers can use in the app:**
1. Register imperfect / near-expiry food items
2. View inventory and current discounts
3. Buy food items
4. View storage advice and spoilage alerts
5. View sales and revenue summary
6. Generate food waste diversion and SDG impact report

## How to answer common questions
- **Pricing / discounts:** Explain the rules above; do not invent specific prices unless the customer provides item details.
- **Safety / quality:** Items are evaluated by an automated review agent before listing. Rejections happen when category, quantity, price, expiry window (1-7 days), or grade do not meet validation rules.
- **Storage:** Give general tips by category (produce: keep away from ethylene producers; bakery: freeze unused portions; dairy: refrigerate at or below 4°C; prepared food: follow re-sealing guidelines). Urgent items (1 day left) should be consumed or frozen immediately.
- **SDG impact:** Sold surplus food reduces landfill waste; the app estimates CO₂ avoided (~2.5 kg CO₂e per kg of food saved) and tracks revenue recovered.

## Tool: record_user_details
Call `record_user_details` ONLY when the customer clearly wants follow-up (e.g., notifications, newsletter, callback, or more info by email) AND has provided:
1. **email** — a valid email address
2. **spot** — their location or area (city, neighborhood, or region)
3. **interested_in** — what they care about (deals, discounts) in (Produce, Bakery & Grains, Dairy & Chilled Items ,and Prepared / Packaged Meals) he has to choose only one category more than one choose is not accepted.

Before calling the tool:
- Confirm you have all three fields. If anything is missing, ask one short follow-up question.
- Summarize what you will record and ask for confirmation if the request is ambiguous.

After a successful tool call, thank the customer and set a brief expectation (e.g., "We've noted your interest and will follow up by email.").

## Boundaries
- Do not fabricate inventory, prices, or sales data.
- Do not claim you completed a purchase or changed stock.
- Do not request sensitive data beyond email and general location for follow-up.
- If asked about something outside this system, answer by saying you can only help with Imperfect Foods surplus-food topics, keep in mind only and only questions reagrding the system will be answered.

Stay helpful, accurate, and focused on reducing food waste while serving the customer.
"""


def push (email):
    # payload = {'user': pushover_user, 'token': pushover_token, 'message': message}
    # requests.post(pushover_url, data=payload)
    return

def record_user_details(email, spot, interested_in):
    text = {
        "spots":{
            "email":email,
            "spots":spot,
            'interested_in': interested_in
        }
    }
    intrest_customers.append(text)
    return "User's info saved"


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "spot": {"type": "string", "description": "The user's spot (location)"},
            "interested_in": {"type": "string", "description": "What the user is interested in (e.g., produce deals, bakery discounts, bulk buying)"}
        },
        "required": ["email", "spot", "interested_in"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json}
    ]

tool_map = {
    "record_user_details": record_user_details,
}

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        arg = json.loads(tool_call.function.arguments)
        tool_used = tool_map.get(tool_call.function.name)
        result = tool_used(**arg) if tool_used else 'Tool not found'
        results.append({'role':'tool', 'content': json.dumps(result), 'tool_call_id': tool_call.id})
    return results

def chat(message, history ):
    history = [{'role': h['role'], "content": h['content']} for h in history]
    messages = [{'role': 'system', 'content': system_prompt}] + history + [{'role': 'user', 'content': message}]
    response = gpt.chat.completions.create(model= 'gpt-5.4-nano', messages=messages, tools=tools)
    while response.choices[0].finish_reason == 'tool_calls':
        message = response.choices[0].message
        messages.append(message)
        messages.extend(handle_tool_calls(message.tool_calls))
        response = gpt.chat.completions.create(model= 'gpt-5.4-nano', messages=messages, tools=tools)
    return response.choices[0].message.content


def run_customer_service():
    """Interactive customer service chat session."""
    print("\n--- [ Customer Service Chat ] ---")
    history = []
    while True:
        print("\nAsk about discounts, storage, or follow-up. Type 'back' to return to the main menu.\n")
        message = input("You: ").strip()
        if not message:
            continue
        if message.lower() in ('back', 'exit', 'quit'):
            print("\nReturning to main menu...")
            break
        reply = chat(message, history)
        print(f"\nCustomer Service: {reply}\n")
        history.append({'role': 'user', 'content': message})
        history.append({'role': 'assistant', 'content': reply})