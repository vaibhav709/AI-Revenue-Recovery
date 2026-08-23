import json

def calculate_priority_score(
    failure_probability: float,
    amount_at_risk: float,
    max_amount_in_batch: float,
    attempt_count: int,
    status: str
) -> dict:
    # 1. RISK SCORE
    risk_score = failure_probability * 50.0
    risk_score = max(0.0, min(50.0, risk_score))
    
    # 2. FINANCIAL EXPOSURE SCORE
    amount_at_risk = max(0.0, float(amount_at_risk))
    max_amount_in_batch = max(0.0, float(max_amount_in_batch))
    
    if max_amount_in_batch == 0:
        financial_exposure_score = 0.0
    else:
        financial_exposure_score = (amount_at_risk / max_amount_in_batch) * 30.0
        
    financial_exposure_score = max(0.0, min(30.0, financial_exposure_score))
    
    # 3. URGENCY SCORE
    escalation_score = 10 if status == "Escalated" else 0
    attempt_score = min(attempt_count * 2, 10)
    urgency_score = escalation_score + attempt_score
    urgency_score = min(20, urgency_score)
    
    # 4. FINAL SCORE
    total_score = risk_score + financial_exposure_score + urgency_score
    total_score_int = int(round(max(0.0, min(100.0, total_score))))
    
    # TIERS
    if total_score_int >= 80:
        tier = "CRITICAL"
    elif total_score_int >= 60:
        tier = "HIGH"
    elif total_score_int >= 40:
        tier = "MEDIUM"
    else:
        tier = "LOW"
        
    factors = {
        "risk_score": round(risk_score, 2),
        "financial_exposure_score": round(financial_exposure_score, 2),
        "urgency_score": urgency_score,
        "attempt_score": attempt_score,
        "escalation_score": escalation_score
    }
    
    return {
        "priority_score": total_score_int,
        "priority_tier": tier,
        "priority_factors": json.dumps(factors)
    }

def update_active_case_analytics(existing_case, new_analytics: dict):
    """
    Updates ONLY the analytical/risk fields of an active RecoveryCase.
    Preserves workflow, history, and AI recommendation fields.
    """
    # Safe analytical fields to update
    safe_fields = {
        "failure_probability",
        "predicted_failure",
        "risk_level",
        "priority",
        "priority_score",
        "priority_tier",
        "priority_factors",
        "amount_at_risk",
        "strategy",
        "communication_channel",
        "follow_up_days",
        "escalation_candidate",
        "final_action",
        "customer_message",
        "follow_up_action"
    }
    
    for key, value in new_analytics.items():
        if key in safe_fields:
            setattr(existing_case, key, value)
            
    return existing_case
