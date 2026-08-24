
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

import json
from sqlalchemy.orm import Session
from openai import OpenAI
from typing import Dict, Any

from api.services.portfolio_analytics import get_portfolio_analytics

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)

def generate_portfolio_insights(db: Session) -> Dict[str, Any]:
    # 1. Gather deterministic context
    analytics = get_portfolio_analytics(db)
    
    kpis = analytics.get("kpis", {})
    if kpis.get("total_cases", 0) == 0:
        return {
            "success": True,
            "available": False,
            "reason": "No portfolio data available."
        }
    
    # 2. Build the context string
    # Important: Emphasize INR currency to the model.
    context_str = f"""
PORTFOLIO CONTEXT:
- All monetary values are in Indian Rupees (INR).
- Total Cases: {kpis.get('total_cases')}
- Active Cases: {kpis.get('active_cases')}
- Completed Cases: {kpis.get('completed_cases')}
- Escalated Cases: {kpis.get('escalated_cases')}
- Total Amount at Risk: ₹{kpis.get('total_amount_at_risk')}
- Total Amount Recovered: ₹{kpis.get('total_amount_recovered')}
- Recovery Rate: {kpis.get('recovery_rate')}%

DISTRIBUTIONS:
- Risk Distribution: {analytics.get('distributions', {}).get('risk')}
- Priority Distribution: {analytics.get('distributions', {}).get('priority')}

ACTIONS/EXECUTIONS:
- Pending Actions: {kpis.get('pending_actions')}
- Executed Actions: {kpis.get('executed_actions')}
- Failed Executions: {kpis.get('failed_actions')}

TOP CASES (At Risk):
"""
    for case in analytics.get("lists", {}).get("top_cases", []):
        context_str += f" - Case {case['id']}: Customer {case['customer_name']} | Risk: {case['risk_level']} | At Risk: ₹{case['amount_at_risk']} | Attempts: {case['attempt_count']} | Status: {case['status']}\n"
    
    context_str += "\nPENDING ACTIONS:\n"
    for pa in analytics.get("lists", {}).get("pending_actions", []):
        context_str += f" - Case {pa['case_id']}: {pa['action_type']} via {pa['channel']} (Overdue: {pa['is_overdue']})\n"
        
    prompt = f"""
You are an advisory AI Portfolio Intelligence engine. 
Based on the following deterministic portfolio metrics (all monetary values are INR), generate an advisory assessment.
Identify risk concentrations, repeated failures, overdue actions, and provide human-focused recommendations.

{context_str}

Respond with a JSON object strictly adhering to this schema:
{{
  "portfolio_summary": "Overall summary of the portfolio...",
  "key_findings": [
    {{
      "title": "Short title",
      "description": "Detailed description",
      "severity": "HIGH|MEDIUM|LOW",
      "case_ids": [1, 2, ...]
    }}
  ],
  "recommended_focus": [
    {{
      "case_id": 1,
      "reason": "Reason for focus",
      "priority": "HIGH|MEDIUM|LOW"
    }}
  ],
  "risk_observations": ["obs 1", "obs 2"],
  "recovery_observations": ["obs 1", "obs 2"],
  "human_actions": ["action 1", "action 2"],
  "confidence": 0.95
}}
"""
    # 3. Call OpenAI
    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model="gpt-5.6-luna",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a portfolio intelligence engine. Output JSON only."},
                {"role": "user", "content": prompt}
            ]
        )
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {str(e)}")
        
    # 4. Parse and Validate Response
    try:
        raw_content = response.choices[0].message.content
        response_json = json.loads(raw_content)
    except Exception as e:
        raise ValueError(f"Invalid JSON returned by AI: {str(e)}")
        
    # Field existence
    required_fields = ["portfolio_summary", "key_findings", "recommended_focus", "risk_observations", "recovery_observations", "human_actions", "confidence"]
    for field in required_fields:
        if field not in response_json:
            raise ValueError(f"Missing required field in AI response: {field}")
            
    # Validate confidence
    confidence = response_json["confidence"]
    if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
        raise ValueError(f"Invalid confidence value: {confidence}")
        
    # Validate enums in key_findings
    for kf in response_json["key_findings"]:
        if "title" not in kf or "description" not in kf or "severity" not in kf or "case_ids" not in kf:
             raise ValueError("Malformed key_finding object")
        if kf["severity"] not in ["HIGH", "MEDIUM", "LOW"]:
            raise ValueError(f"Invalid severity enum: {kf['severity']}")
            
    # Validate enums in recommended_focus
    for rf in response_json["recommended_focus"]:
        if "case_id" not in rf or "reason" not in rf or "priority" not in rf:
             raise ValueError("Malformed recommended_focus object")
        if rf["priority"] not in ["HIGH", "MEDIUM", "LOW"]:
            raise ValueError(f"Invalid priority enum: {rf['priority']}")

    # 5. Return success wrapper
    return {
        "success": True,
        "available": True,
        "insights": response_json
    }
