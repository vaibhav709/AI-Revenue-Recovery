import os
import json
from sqlalchemy.orm import Session
from typing import Dict, Any
from openai import OpenAI

from api.models import RecoveryCase, Customer

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)

def _build_gpt_prompt(case: RecoveryCase, customer: Customer) -> str:
    prompt = f"""
Analyze the following recovery case and provide a decision on whether to CONTINUE, STOP, or ESCALATE the automated recovery process.

Rules:
- You must output exactly valid JSON.
- Allowed decision values: "CONTINUE", "STOP", "ESCALATE".
- Output keys must be: "decision", "reason", "recommended_action", "confidence".
- Confidence must be a float between 0.0 and 1.0.
- Do NOT override deterministic safety rules.

Case Data:
- failure_probability: {case.failure_probability}
- predicted_failure: {case.predicted_failure}
- risk_level: {case.risk_level}
- priority_score: {case.priority_score}
- priority_tier: {case.priority_tier}
- priority_factors: {case.priority_factors}
- amount_at_risk: {case.amount_at_risk}
- amount_recovered: {case.amount_recovered}
- attempt_count: {case.attempt_count}
- max_attempts: {case.max_attempts}
- strategy: {case.strategy}
- communication_channel: {case.communication_channel}
- follow_up_days: {case.follow_up_days}

Customer Metrics:
- bill_amount_1: {customer.bill_amount_1}
- pay_status_1: {customer.pay_status_1}
"""
    return prompt

def evaluate_recovery_case(case: RecoveryCase, customer: Customer, db: Session) -> Dict[str, Any]:
    # 1. Deterministic Safety Boundaries
    if case.amount_recovered >= case.amount_at_risk:
        return {
            "success": True, "case_id": case.id, "decision": "STOP",
            "reason": "Recovery target has been reached.", "source": "deterministic_rule"
        }
    
    if case.status == "Completed":
        return {
            "success": True, "case_id": case.id, "decision": "STOP",
            "reason": "Case is already completed.", "source": "deterministic_rule"
        }
        
    if case.status == "Escalated":
        return {
            "success": True, "case_id": case.id, "decision": "ESCALATE",
            "reason": "Case is already escalated.", "source": "deterministic_rule"
        }
        
    if case.attempt_count >= case.max_attempts:
        return {
            "success": True, "case_id": case.id, "decision": "ESCALATE",
            "reason": "Maximum recovery attempts reached.", "source": "deterministic_rule"
        }
        
    # 2. GPT Execution
    try:
        client = get_openai_client()
    except ValueError as e:
        raise ValueError(f"Configuration error: {str(e)}")
        
    prompt = _build_gpt_prompt(case, customer)
    
    try:
        response = client.chat.completions.create(
            model="gpt-5.6-luna",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a recovery decision engine. Output JSON only."},
                {"role": "user", "content": prompt}
            ]
            # No temperature parameter supplied
        )
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {str(e)}")
        
    try:
        raw_content = response.choices[0].message.content
        response_json = json.loads(raw_content)
    except Exception as e:
        raise ValueError(f"Invalid JSON returned by AI: {str(e)}")
        
    decision = response_json.get("decision")
    reason = response_json.get("reason")
    recommended_action = response_json.get("recommended_action")
    confidence = response_json.get("confidence")
    
    # 3. Validation
    if decision not in ["CONTINUE", "STOP", "ESCALATE"]:
        raise ValueError(f"Invalid decision returned by AI: {decision}")
        
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        raise ValueError("Invalid confidence score returned by AI.")
        
    if not (0.0 <= confidence <= 1.0):
        raise ValueError("Invalid confidence score returned by AI. Must be between 0 and 1.")
        
    # 4. Persistence
    case.ai_decision = decision
    case.ai_reasoning = reason
    case.ai_recommended_action = recommended_action
    case.ai_confidence = confidence
    db.commit()
    
    return {
        "success": True,
        "case_id": case.id,
        "decision": decision,
        "reason": reason,
        "recommended_action": recommended_action,
        "confidence": confidence,
        "source": "gpt-5.6-luna"
    }

def orchestrate_active_cases(db: Session) -> Dict[str, Any]:
    # Use existing active-case concept
    cases = db.query(RecoveryCase).all()
    active_cases = [c for c in cases if c.status != "Completed" and c.amount_recovered < c.amount_at_risk]
    
    # Sort by priority_score DESC
    active_cases.sort(key=lambda c: c.priority_score if c.priority_score is not None else -1, reverse=True)
    
    stats = {
        "total_cases": len(active_cases),
        "eligible_cases": 0,
        "processed": 0,
        "continue": 0,
        "stop": 0,
        "escalate": 0,
        "skipped": 0,
        "errors": 0
    }
    
    for case in active_cases:
        customer = db.query(Customer).filter(Customer.customer_id == case.customer_id).first()
        if not customer:
            stats["skipped"] += 1
            continue
            
        try:
            res = evaluate_recovery_case(case, customer, db)
            if res.get("source") == "deterministic_rule":
                stats["skipped"] += 1
            else:
                stats["eligible_cases"] += 1
                stats["processed"] += 1
                dec = res["decision"].lower()
                if dec == "continue":
                    stats["continue"] += 1
                elif dec == "stop":
                    stats["stop"] += 1
                elif dec == "escalate":
                    stats["escalate"] += 1
        except Exception:
            # If it threw an error and wasn't skipped by deterministic rules,
            # it was eligible but failed processing.
            if case.amount_recovered < case.amount_at_risk and case.status != "Completed" and case.status != "Escalated" and case.attempt_count < case.max_attempts:
                stats["eligible_cases"] += 1
            stats["errors"] += 1
            
    return stats
