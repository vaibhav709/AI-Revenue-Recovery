import datetime
from sqlalchemy.orm import Session
from api.models import RecoveryAction, ExecutionAttempt
from api.services.action_executor import execute_recovery_action

def process_scheduled_recovery_actions(db: Session, batch_size: int = 10) -> dict:
    batch_size = max(1, min(batch_size, 50))
    now = datetime.datetime.now(datetime.timezone.utc)
    
    eligible_actions = db.query(RecoveryAction).filter(
        RecoveryAction.status == "PENDING",
        RecoveryAction.scheduled_for.isnot(None),
        RecoveryAction.scheduled_for <= now
    ).order_by(RecoveryAction.scheduled_for.asc()).limit(batch_size).all()
    
    results = []
    skipped = 0
    failed = 0
    processed = 0
    
    for action in eligible_actions:
        # Re-verify state for concurrency safety
        db.refresh(action)
        if action.status != "PENDING":
            skipped += 1
            continue
            
        try:
            res = execute_recovery_action(action, db)
            db.refresh(action)
            
            attempt = db.query(ExecutionAttempt).filter_by(action_id=action.id).order_by(ExecutionAttempt.id.desc()).first()
            exec_status = attempt.execution_status if attempt else "UNKNOWN"
            
            # According to Executor logic, a SKIPPED execution (like NO_ACTION) is not a true failure.
            # Only FAILED or BLOCKED are counted as failed.
            if exec_status in ["FAILED", "BLOCKED"]:
                failed += 1
                
            results.append({
                "action_id": action.id,
                "status": action.status,
                "execution_status": exec_status
            })
            processed += 1
            
        except Exception as e:
            failed += 1
            results.append({
                "action_id": action.id,
                "status": action.status,
                "execution_status": "EXCEPTION",
                "error": str(e)
            })
            
    return {
        "success": True,
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
        "results": results
    }
