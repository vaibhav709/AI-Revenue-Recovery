import datetime
from sqlalchemy.orm import Session
from api.models import RecoveryCase

def process_recovery_attempt(case: RecoveryCase, db: Session, commit: bool = True):
    # RULE 1: FULL RECOVERY
    if case.amount_recovered >= case.amount_at_risk :
        return {
            "decision": "STOP",
            "attempt_count": case.attempt_count,
            "max_attempts": case.max_attempts,
            "message": "Recovery target has already been fully recovered."
        }
        
    # RULE 2: CASE COMPLETED
    if case.status == "Completed":
        return {
            "decision": "STOP",
            "attempt_count": case.attempt_count,
            "max_attempts": case.max_attempts,
            "message": "Case is already completed."
        }
        
    # RULE 3: CASE ESCALATED
    if case.status == "Escalated":
        return {
            "decision": "STOP",
            "attempt_count": case.attempt_count,
            "max_attempts": case.max_attempts,
            "message": "Case is already escalated."
        }
        
    # RULE 4: MAXIMUM ATTEMPTS
    if case.attempt_count >= case.max_attempts:
        if case.amount_recovered < case.amount_at_risk:
            case.status = "Escalated"
            case.recovery_status = "Escalated"
            case.escalation_reason = "Maximum recovery attempts reached without full recovery."
            if commit:
                db.commit()
            return {
                "decision": "ESCALATE",
                "attempt_count": case.attempt_count,
                "max_attempts": case.max_attempts,
                "message": "Maximum recovery attempts reached. Further recovery attempts have been stopped.",
                "escalation_reason": case.escalation_reason
            }
        else:
            return {
                "decision": "STOP",
                "attempt_count": case.attempt_count,
                "max_attempts": case.max_attempts,
                "message": "Maximum recovery attempts reached, but recovery is complete."
            }
            
    # RULE 5: CONTINUE
    case.attempt_count += 1
    case.last_attempt_at = datetime.datetime.utcnow()
    
    # Check boundaries immediately after incrementing
    if case.attempt_count >= case.max_attempts and case.amount_recovered < case.amount_at_risk:
        case.status = "Escalated"
        case.recovery_status = "Escalated"
        case.escalation_reason = "Maximum recovery attempts reached without full recovery."
        if commit:
            db.commit()
        return {
            "decision": "ESCALATE",
            "attempt_count": case.attempt_count,
            "max_attempts": case.max_attempts,
            "message": "Maximum recovery attempts reached. Further recovery attempts have been stopped.",
            "escalation_reason": case.escalation_reason
        }
    
    if commit:
        db.commit()
    return {
        "decision": "CONTINUE",
        "attempt_count": case.attempt_count,
        "max_attempts": case.max_attempts,
        "message": "Recovery attempt recorded."
    }
