from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any

from api.models import RecoveryCase, RecoveryAction, ExecutionAttempt, Customer

def get_portfolio_analytics(db: Session) -> Dict[str, Any]:
    # 1. Base Aggregations
    total_cases = db.query(func.count(RecoveryCase.id)).scalar() or 0
    active_cases = db.query(func.count(RecoveryCase.id)).filter(
        RecoveryCase.status.notin_(["Completed"])
    ).scalar() or 0
    completed_cases = db.query(func.count(RecoveryCase.id)).filter(
        RecoveryCase.status == "Completed"
    ).scalar() or 0
    escalated_cases = db.query(func.count(RecoveryCase.id)).filter(
        RecoveryCase.status == "Escalated"
    ).scalar() or 0

    # 2. Financial Aggregations
    total_amount_at_risk = db.query(func.sum(RecoveryCase.amount_at_risk)).scalar() or 0.0
    total_amount_recovered = db.query(func.sum(RecoveryCase.amount_recovered)).scalar() or 0.0
    remaining_amount_at_risk = total_amount_at_risk - total_amount_recovered
    if remaining_amount_at_risk < 0:
        remaining_amount_at_risk = 0.0

    if total_amount_at_risk > 0:
        recovery_rate = (total_amount_recovered / total_amount_at_risk) * 100
    else:
        recovery_rate = 0.0

    # 3. Action / Execution Aggregations
    total_recovery_attempts = db.query(func.sum(RecoveryCase.attempt_count)).scalar() or 0
    
    pending_actions = db.query(func.count(RecoveryAction.id)).filter(RecoveryAction.status == "PENDING").scalar() or 0
    executed_actions = db.query(func.count(RecoveryAction.id)).filter(RecoveryAction.status == "EXECUTED").scalar() or 0
    
    failed_actions = db.query(func.count(ExecutionAttempt.id)).filter(ExecutionAttempt.execution_status == "FAILED").scalar() or 0
    blocked_actions = db.query(func.count(ExecutionAttempt.id)).filter(ExecutionAttempt.execution_status == "BLOCKED").scalar() or 0
    skipped_actions = db.query(func.count(ExecutionAttempt.id)).filter(ExecutionAttempt.execution_status == "SKIPPED").scalar() or 0

    # 4. Distributions
    risk_dist_query = db.query(RecoveryCase.risk_level, func.count(RecoveryCase.id)).group_by(RecoveryCase.risk_level).all()
    risk_distribution = {row[0]: row[1] for row in risk_dist_query if row[0]}
    
    priority_dist_query = db.query(RecoveryCase.priority_tier, func.count(RecoveryCase.id)).group_by(RecoveryCase.priority_tier).all()
    priority_distribution = {row[0]: row[1] for row in priority_dist_query if row[0]}
    
    execution_dist_query = db.query(ExecutionAttempt.execution_status, func.count(ExecutionAttempt.id)).group_by(ExecutionAttempt.execution_status).all()
    execution_status_distribution = {row[0]: row[1] for row in execution_dist_query if row[0]}

    # 5. Top Cases Requiring Attention (Limit 10)
    top_cases_query = db.query(RecoveryCase, Customer).outerjoin(Customer, RecoveryCase.customer_id == Customer.customer_id).filter(
        RecoveryCase.status.notin_(["Completed"])
    ).order_by(
        desc(RecoveryCase.amount_at_risk),
        desc(RecoveryCase.priority_score)
    ).limit(10).all()
    
    top_cases = []
    for c, cust in top_cases_query:
        top_cases.append({
            "id": c.id,
            "customer_id": c.customer_id,
            "customer_name": cust.nickname if cust and cust.nickname else f"Customer {c.customer_id}",
            "risk_level": c.risk_level,
            "priority": c.priority,
            "amount_at_risk": c.amount_at_risk,
            "amount_recovered": c.amount_recovered,
            "attempt_count": c.attempt_count,
            "status": c.status
        })

    # 6. Pending Actions (Limit 10) - Overdue first, then earliest
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    # SQLAlchemy doesn't cleanly sort by "overdue" natively without case/when, 
    # but we can sort by scheduled_for ASC which natively puts earliest/overdue first.
    pending_actions_query = db.query(RecoveryAction, RecoveryCase, Customer)\
        .join(RecoveryCase, RecoveryAction.case_id == RecoveryCase.id)\
        .outerjoin(Customer, RecoveryCase.customer_id == Customer.customer_id)\
        .filter(RecoveryAction.status == "PENDING")\
        .order_by(RecoveryAction.scheduled_for.asc())\
        .limit(10).all()
        
    pending_actions_list = []
    for a, c, cust in pending_actions_query:
        
        is_overdue = False
        if a.scheduled_for:
            if a.scheduled_for.tzinfo is None:
                is_overdue = a.scheduled_for.replace(tzinfo=datetime.timezone.utc) <= now
            else:
                is_overdue = a.scheduled_for <= now

        pending_actions_list.append({
            "id": a.id,
            "case_id": c.id,
            "customer_name": cust.nickname if cust and cust.nickname else f"Customer {c.customer_id}",
            "action_type": a.action_type,
            "channel": a.channel,
            "scheduled_for": a.scheduled_for.isoformat() if a.scheduled_for else None,
            "status": a.status,
            "is_overdue": bool(is_overdue)
        })

    # 7. Recent Execution Activity (Limit 10)
    recent_activity_query = db.query(ExecutionAttempt, RecoveryAction, RecoveryCase, Customer)\
        .join(RecoveryAction, ExecutionAttempt.action_id == RecoveryAction.id)\
        .join(RecoveryCase, RecoveryAction.case_id == RecoveryCase.id)\
        .outerjoin(Customer, RecoveryCase.customer_id == Customer.customer_id)\
        .order_by(desc(ExecutionAttempt.attempted_at))\
        .limit(10).all()
        
    recent_activity = []
    for ex, a, c, cust in recent_activity_query:
        recent_activity.append({
            "id": ex.id,
            "time": ex.attempted_at.isoformat() if ex.attempted_at else None,
            "case_id": c.id,
            "customer_name": cust.nickname if cust and cust.nickname else f"Customer {c.customer_id}",
            "action_type": a.action_type,
            "channel": ex.channel or a.channel,
            "result": ex.execution_status
        })

    return {
        "kpis": {
            "total_cases": total_cases,
            "active_cases": active_cases,
            "completed_cases": completed_cases,
            "escalated_cases": escalated_cases,
            "total_amount_at_risk": total_amount_at_risk,
            "total_amount_recovered": total_amount_recovered,
            "remaining_amount_at_risk": remaining_amount_at_risk,
            "recovery_rate": recovery_rate,
            "total_recovery_attempts": total_recovery_attempts,
            "pending_actions": pending_actions,
            "executed_actions": executed_actions,
            "failed_actions": failed_actions,
            "blocked_actions": blocked_actions,
            "skipped_actions": skipped_actions
        },
        "distributions": {
            "risk": risk_distribution,
            "priority": priority_distribution,
            "execution": execution_status_distribution
        },
        "lists": {
            "top_cases": top_cases,
            "pending_actions": pending_actions_list,
            "recent_activity": recent_activity
        }
    }
