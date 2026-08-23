import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from api.models import RecoveryCase, RecoveryAction

def _serialize_action(action: RecoveryAction) -> Dict[str, Any]:
    return {
        "id": action.id,
        "action_type": action.action_type,
        "decision": action.decision,
        "channel": action.channel,
        "status": action.status,
        "scheduled_for": action.scheduled_for.isoformat() if action.scheduled_for else None,
        "description": action.description
    }

def plan_recovery_action(case: RecoveryCase, orchestration_decision: str, db: Session) -> Dict[str, Any]:
    # 1. Safety Boundaries (MUST independently verify FIRST)
    if case.amount_recovered >= case.amount_at_risk or case.status == "Completed":
        decision = "STOP"
    elif case.status == "Escalated" or case.attempt_count >= case.max_attempts:
        decision = "ESCALATE"
    else:
        # 2. Decision Validation
        decision = orchestration_decision.upper() if orchestration_decision else ""
        if decision not in ["CONTINUE", "STOP", "ESCALATE"]:
            raise ValueError(f"Invalid orchestration decision: {decision}")
        
    # 3. Duplicate Action Prevention
    existing_action = db.query(RecoveryAction).filter(
        RecoveryAction.case_id == case.id,
        RecoveryAction.status == "PENDING"
    ).first()
    
    if existing_action:
        return _serialize_action(existing_action)

    # 4. Determine Action Details
    action_type = ""
    channel = None
    scheduled_for = None
    description = ""
    
    if decision == "CONTINUE":
        action_type = "RECOVERY_CONTACT"
        channel = case.communication_channel
        if case.follow_up_days is not None:
            scheduled_for = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=case.follow_up_days)
        description = "Prepare recovery contact using the existing recovery strategy."
    elif decision == "STOP":
        action_type = "NO_ACTION"
        description = "No further action required."
    elif decision == "ESCALATE":
        action_type = "ESCALATION_REVIEW"
        description = "Escalation review required."

    # 5. Create Action
    new_action = RecoveryAction(
        case_id=case.id,
        action_type=action_type,
        decision=decision,
        channel=channel,
        description=description,
        status="PENDING",
        scheduled_for=scheduled_for
    )
    
    db.add(new_action)
    db.commit()
    db.refresh(new_action)
    
    return _serialize_action(new_action)


def plan_pending_recovery_actions(db: Session) -> Dict[str, Any]:
    # Process only active cases that have an orchestration decision
    active_cases = db.query(RecoveryCase).filter(
        RecoveryCase.ai_decision.isnot(None),
        RecoveryCase.status != "Completed",
        RecoveryCase.amount_recovered < RecoveryCase.amount_at_risk
    ).all()
    
    # Sort by priority_score DESC
    active_cases.sort(key=lambda c: c.priority_score if c.priority_score is not None else -1, reverse=True)
    
    stats = {
        "total_cases": len(active_cases),
        "actions_created": 0,
        "actions_reused": 0,
        "no_action": 0,
        "escalation_reviews": 0,
        "errors": 0
    }
    
    for case in active_cases:
        try:
            existing = db.query(RecoveryAction).filter(
                RecoveryAction.case_id == case.id,
                RecoveryAction.status == "PENDING"
            ).first()
            
            if existing:
                stats["actions_reused"] += 1
                if existing.action_type == "NO_ACTION":
                    stats["no_action"] += 1
                elif existing.action_type == "ESCALATION_REVIEW":
                    stats["escalation_reviews"] += 1
                continue
                
            action = plan_recovery_action(case, case.ai_decision, db)
            
            stats["actions_created"] += 1
            if action["action_type"] == "NO_ACTION":
                stats["no_action"] += 1
            elif action["action_type"] == "ESCALATION_REVIEW":
                stats["escalation_reviews"] += 1
        except Exception as e:
            stats["errors"] += 1
            
    return stats
