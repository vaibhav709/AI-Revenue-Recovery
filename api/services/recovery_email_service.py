import os
from api.models import RecoveryCase, Customer

def format_inr(amount: float) -> str:
    try:
        val = int(amount) if amount else 0
        s = str(val)
        if len(s) > 3:
            s_head = s[:-3]
            s_tail = s[-3:]
            parts = []
            while len(s_head) > 2:
                parts.insert(0, s_head[-2:])
                s_head = s_head[:-2]
            if s_head:
                parts.insert(0, s_head)
            return "₹" + ",".join(parts) + "," + s_tail
        else:
            return "₹" + s
    except:
        return f"₹{amount}"

def determine_communication_intent(case: RecoveryCase) -> str:
    # 1. Fully recovered / completed
    if case.status == "Completed" or (case.amount_recovered is not None and case.amount_at_risk is not None and case.amount_recovered >= case.amount_at_risk and case.amount_at_risk > 0):
        return "CASE_RESOLUTION"
    
    # 2. Escalated
    if case.status == "Escalated" or (case.attempt_count is not None and case.max_attempts is not None and case.attempt_count >= case.max_attempts):
        return "ESCALATION_NOTICE"
        
    # Note: PROMISE_REMINDER and MISSED_PROMISE are not implemented because promise-to-pay fields do not exist yet in the data model.

    # 3. Existing follow-up is due
    if case.attempt_count is not None and case.attempt_count > 0:
        if case.risk_level == "HIGH":
            return "URGENT_RECOVERY"
        return "FOLLOW_UP_REMINDER"
        
    # 4. First recovery contact
    if case.risk_level == "HIGH":
        return "URGENT_RECOVERY"
    
    if case.risk_level == "MEDIUM":
        return "PAYMENT_ASSISTANCE"
    
    return "PAYMENT_REMINDER"

def build_email_context(case: RecoveryCase, customer: Customer) -> dict:
    intent = determine_communication_intent(case)
    recipient = os.getenv("RECOVERY_TEST_EMAIL", "test@example.com")
    cust_name = customer.nickname if customer and customer.nickname else ""
    outstanding = (case.amount_at_risk or 0.0) - (case.amount_recovered or 0.0)
    if outstanding < 0:
        outstanding = 0.0
        
    return {
        "intent": intent,
        "recipient": recipient,
        "customer_name": cust_name,
        "amount_at_risk": format_inr(case.amount_at_risk),
        "amount_recovered": format_inr(case.amount_recovered),
        "outstanding_amount": format_inr(outstanding),
        "ai_message": case.ai_customer_message
    }

def prepare_recovery_email(case: RecoveryCase, customer: Customer) -> dict:
    ctx = build_email_context(case, customer)
    intent = ctx["intent"]
    
    greeting = f"Hello {ctx['customer_name']}," if ctx['customer_name'] else "Hello,"
    subject = "Payment Notice"
    body = ""
    
    if intent == "CASE_RESOLUTION":
        subject = "Recovery Case Resolved"
        body = f"{greeting}\n\nWe are confirming that your recovery case has been successfully resolved. Your account is in good standing.\n\nThank you for your cooperation."
    elif intent == "PAYMENT_CONFIRMATION":
        subject = "Payment Confirmation"
        body = f"{greeting}\n\nWe confirm receipt of your recent payment. Your outstanding balance is now {ctx['outstanding_amount']}.\n\nThank you."
    elif intent == "ESCALATION_NOTICE":
        subject = "Account Recovery Review"
        body = f"{greeting}\n\nYour account requires additional review. The outstanding amount is {ctx['outstanding_amount']}.\n\nPlease contact support to address this immediately."
    elif intent == "URGENT_RECOVERY":
        subject = "Urgent Payment Follow-up"
        body = f"{greeting}\n\nThis is an urgent notice regarding your account. We need to clear the outstanding balance of {ctx['outstanding_amount']}.\n\nPlease prioritize this payment."
    elif intent == "FOLLOW_UP_REMINDER":
        subject = "Payment Follow-up"
        body = f"{greeting}\n\nThis is a follow-up to our previous communication. You currently have an outstanding balance of {ctx['outstanding_amount']}.\n\nPlease complete your payment at your earliest convenience."
    elif intent == "PAYMENT_ASSISTANCE":
        subject = "Payment Assistance"
        body = f"{greeting}\n\nWe noticed a pending balance of {ctx['outstanding_amount']}. If you need any assistance or flexible options, we are here to help.\n\nPlease let us know how we can support you."
    else: # PAYMENT_REMINDER
        subject = "Payment Reminder"
        body = f"{greeting}\n\nThis is a friendly reminder that a payment requires attention. Your current outstanding balance is {ctx['outstanding_amount']}.\n\nPlease review your payment method and complete the payment."

    if ctx["ai_message"] and ctx["ai_message"].strip():
        body += f"\n\nNote:\n{ctx['ai_message'].strip()}"

    return {
        "intent": intent,
        "recipient": ctx["recipient"],
        "subject": subject,
        "body": body
    }
