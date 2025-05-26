from openai import OpenAI
import json
import re
from langchain.tools import Tool

def parse_purchases(user_input: str):
    prompt = f"""
    Extract all purchases from the following text. For each purchase, return a JSON object with:
    - amount (number)
    - currency (string, default to "USD" if not specified)
    - category (string, e.g. 'transportation', 'food', etc. Guess if not specified)
    - description (string, only describe the purchase, not the amount/currency/category)

    If there are multiple purchases, return a JSON array of objects.

    Purchases: "{user_input}"
    JSON:
    """
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0,
    )
    content = response.choices[0].message.content
    import json, re
    match = re.search(r'\[.*\]|\{.*\}', content, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        raise ValueError("No JSON found in AI response")
    
parse_purchase_tool = Tool(
    name="parse_purchase",
    func= parse_purchases,
    description="Parse a natural language purchase description into a JSON object with fields: amount, currency, category, description."
)
    
if __name__ == "__main__":
    print(parse_purchases("I bought a new phone for $500"))