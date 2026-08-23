import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def generate_ai_action_internal(case_data: dict, customer_data: dict) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("AI recovery service is not configured.")
        
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    if model != "gpt-5.6-luna":
        # Force the required model
        model = "gpt-5.6-luna"

    client = OpenAI(api_key=api_key)
    
    system_prompt = """You are the recovery decision engine for a revenue recovery platform.

Analyze the supplied recovery case.
Recommend exactly one bounded next action.
You must not invent customer information.
You must respect the supplied financial values and recovery state.
You must not recommend an action if the case should STOP or ESCALATE.

Allowed decisions: STOP, CONTINUE, ESCALATE.
Provide a structured JSON output matching this schema:
{
  "decision": "CONTINUE",
  "recommended_action": "Send a payment reminder requesting settlement of the outstanding balance.",
  "reason": "The customer has an outstanding balance and recovery is incomplete.",
  "communication_channel": "EMAIL",
  "follow_up_days": 5,
  "customer_message": "Please review your outstanding balance...",
  "confidence": 0.87
}"""

    user_prompt = f"""Customer Information:
- ID: {customer_data.get('customer_id')}
- Credit Limit: {customer_data.get('credit_limit')}
- Recent Bill: {customer_data.get('bill_amount_1')}
- Recent Payment: {customer_data.get('payment_amount_1')}

Risk Information:
- Risk Level: {case_data.get('risk_level')}
- Priority: {case_data.get('priority')}
- Predicted Failure: {case_data.get('predicted_failure')}
- Failure Probability: {case_data.get('failure_probability')}
- Escalation Candidate: {case_data.get('escalation_candidate')}

Recovery Information:
- Amount at Risk: {case_data.get('amount_at_risk')}
- Amount Recovered: {case_data.get('amount_recovered')}
- Attempt Count: {case_data.get('attempt_count')} / {case_data.get('max_attempts')}
- Recovery Status: {case_data.get('recovery_status')}

Existing Pipeline Context:
- Strategy: {case_data.get('strategy')}
- Channel: {case_data.get('communication_channel')}
- Previous Action: {case_data.get('final_action')}
"""

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    try:
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        raise ValueError(f"Failed to parse AI response: {str(e)}")
