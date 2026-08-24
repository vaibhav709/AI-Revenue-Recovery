import os
import json
import resend
from sqlalchemy.orm import Session
from api.services.recovery_attempt import process_recovery_attempt
from api.models import RecoveryAction, RecoveryCase, ExecutionAttempt

def _record_attempt(db, action_id, status, error=None, result=None, channel=None, provider=None, recipient=None, meta=None, should_commit=True):
    attempt = ExecutionAttempt(
        action_id=action_id,
        execution_status=status,
        error=error,
        result=result,
        channel=channel,
        provider=provider,
        recipient=recipient,
        metadata_payload=json.dumps(meta) if meta else None
    )
    db.add(attempt)
    if should_commit:
        db.commit()

def execute_recovery_action(action: RecoveryAction, db: Session) -> dict:
    def finish(success, ret_status, error=None, result=None, exec_status="BLOCKED", provider=None, recipient=None, meta=None, should_commit=True):
        _record_attempt(db, action.id, exec_status, error, result, action.channel, provider, recipient, meta, should_commit)
        ret = {"success": success, "action_id": action.id, "status": ret_status}
        if error: ret["error"] = error
        if result: ret["message"] = result
        if provider: ret["provider"] = provider
        if recipient: ret["recipient"] = recipient
        return ret

    if action.status == "EXECUTED":
        return finish(False, "EXECUTED", error="Action has already been executed.", exec_status="SKIPPED")
    if action.status != "PENDING":
        return finish(False, action.status, error=f"Cannot execute action with status {action.status}.", exec_status="BLOCKED")
    
    # Unsupported action types
    if action.action_type == "NO_ACTION":
        return finish(True, "NO_ACTION", result="No action required.", exec_status="SKIPPED")
    if action.action_type == "ESCALATION_REVIEW":
        return finish(True, "PENDING_REVIEW", result="Escalation review pending.", exec_status="SKIPPED")
    if action.action_type != "RECOVERY_CONTACT":
        return finish(False, action.status, error=f"Unsupported action type: {action.action_type}", exec_status="BLOCKED")
    if action.channel != "EMAIL":
        return finish(False, action.status, error=f"Unsupported channel: {action.channel}", exec_status="BLOCKED")
    
    # Case validation
    case = action.case
    if not case:
        return finish(False, action.status, error="Associated case not found.", exec_status="BLOCKED")
    if case.status == "Completed":
        return finish(False, action.status, error="Case is already completed.", exec_status="BLOCKED")
    if case.amount_recovered >= case.amount_at_risk:
        return finish(False, action.status, error="Case is fully recovered.", exec_status="BLOCKED")
    if case.attempt_count >= case.max_attempts:
        return finish(False, action.status, error="Maximum attempts reached.", exec_status="BLOCKED")
    
    # Env validation
    api_key = os.getenv("RESEND_API_KEY")
    test_email = os.getenv("RECOVERY_TEST_EMAIL")
    if not api_key:
        return finish(False, action.status, error="RESEND_API_KEY is not configured.", exec_status="BLOCKED")
    if not test_email:
        return finish(False, action.status, error="RECOVERY_TEST_EMAIL is not configured.", exec_status="BLOCKED")
    
    # Message fallback
    message = case.ai_customer_message
    if not message or message.strip() == "":
        message = "Hello, this is a test recovery communication from the AI Revenue Recovery system. This message was generated as part of a controlled sandbox execution."
        
    subject = f"Recovery Action Test — Customer {case.customer_id}"
    
    try:
        resend.api_key = api_key
        response = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": test_email,
            "subject": subject,
            "text": message
        })
        
        action.status = "EXECUTED"
        
        provider_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
        meta = {"provider_message_id": provider_id} if provider_id else None
        
        # Don't commit yet inside finish
        ret = finish(True, "EXECUTED", result="Email accepted by Resend", exec_status="SUCCESS", provider="resend", recipient=test_email, meta=meta, should_commit=False)
        
        # Phase 9C: Integrate recovery attempt
        if action.action_type == "RECOVERY_CONTACT":
            process_recovery_attempt(case, db, commit=False)
            
        # Atomic commit for action status, execution attempt, and case attempt updates
        db.commit()
        
        return ret
    except Exception as e:
        # DO NOT update action.status
        return finish(False, "FAILED", error=str(e), exec_status="FAILED", provider="resend", recipient=test_email)
