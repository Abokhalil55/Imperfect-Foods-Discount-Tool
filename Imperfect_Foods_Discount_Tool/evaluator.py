from openai import OpenAI
from dotenv import load_dotenv
import os
import json

def evaluate_added_item(item):
    """Decide either to add the item to the inventory or not"""

    rules = f"""You are an automated review agent evaluating a registered food item entry for a surplus food management system in Malaysia.

Item Data to Review:
- Item Name: {item['name']}
- Category: {item['category']}
- Quantity (kg/units): {item['quantity']}
- Original Price (MYR): {item['original_price']}
- Days Left to Expiry: {item['days_left']}
- Cosmetic Grade: {item['grade']}

Validation Rules:
1. Category Match: The item name MUST logically belong to the selected Category (e.g., "Rice + Chicken" belongs in "Prepared Food", NOT "Produce").
2. Quantity: Must be a positive number greater than 0.
3. Original Price: Must be a realistic, positive number greater than 0 in Malaysian Ringgit (MYR).
4. Days Left: Must be an integer between 1 and 7.
5. Grade: Must be either 'A', 'B', or 'C'.

Your job is to check if all item details strictly follow these validation rules.

Respond with JSON, and ONLY JSON, adhering strictly to one of the following formats:

If ALL fields are valid:
{{"status": "APPROVED", "reason": ""}}

If ANY field violates a rule:
{{"status": "CANCELED", "reason": "One sentence explaining why the item was canceled."}}

Do not include markdown formatting, code blocks (e.g. ```json), or extra text."""

    load_dotenv()
    #ollama = OpenAI(base_url= "http://localhost:11434/v1",api_key=os.getenv("OLLAMA_API_KEY"))
    #ollama_model= 'mistral'
    gpt = OpenAI(base_url= "https://api.openai.com/v1",api_key=os.getenv("gpt_API_KEY"))
    gpt_model= 'gpt-5.4-nano'
    judge_messages = [{"role": "user", "content": rules}]
    response = gpt.chat.completions.create(
        model=gpt_model,
        messages=judge_messages,
        response_format={"type": "json_object"},
    )
    answer = response.choices[0].message.content
    final_result = json.loads(answer)
    return final_result

if __name__ == "__main__":
    main()
