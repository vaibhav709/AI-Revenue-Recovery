"""FastAPI integration for the payment recovery pipeline."""
import traceback
from json import JSONDecodeError

from fastapi import FastAPI, HTTPException, Depends
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func, String

from api.schemas import RecoveryAnalysisRequest
from api.services.recovery_attempt import process_recovery_attempt
from api.services.recovery_orchestrator import evaluate_recovery_case
from api.database import engine, Base, get_db
from api.models import Customer, RecoveryCase, RecoveryAction, ExecutionAttempt, MAX_RECOVERY_ATTEMPTS
from crew.pipeline import CrewAIWorkflowError, run_recovery_pipeline
from crew.rules.recovery_schema import FinalRecoveryPlan
import statistics

def compute_derived_features(d: dict) -> dict:
    data = d.copy()
    pay_statuses = [data[f'pay_status_{i}'] for i in range(1, 7)]
    bill_amounts = [data[f'bill_amount_{i}'] for i in range(1, 7)]
    pay_amounts = [data[f'payment_amount_{i}'] for i in range(1, 7)]
    
    delays = [p for p in pay_statuses if p > 0]
    
    data['num_delayed_payments'] = len(delays)
    data['max_payment_delay'] = max(delays) if delays else 0
    data['avg_payment_delay'] = sum(delays) / 6.0
    data['recent_payment_delay'] = pay_statuses[0] if pay_statuses[0] > 0 else 0
    
    data['avg_bill_amount'] = sum(bill_amounts) / 6.0
    data['avg_payment_amount'] = sum(pay_amounts) / 6.0
    data['total_bill_amount'] = sum(bill_amounts)
    data['total_payment_amount'] = sum(pay_amounts)
    
    # payment_to_bill_ratio: 0 if denominator <= 0, capped between 0 and 5
    if data['total_bill_amount'] > 0:
        val_p2b = data['total_payment_amount'] / data['total_bill_amount']
    else:
        val_p2b = 0.0
    data['payment_to_bill_ratio'] = max(0.0, min(5.0, val_p2b))
        
    # credit_utilization: 0 if denominator <= 0, capped between 0 and 5
    val_cu = data['avg_bill_amount'] / data['credit_limit'] if data['credit_limit'] > 0 else 0.0
    data['credit_utilization'] = max(0.0, min(5.0, val_cu))
    
    data['payment_std'] = statistics.stdev(pay_amounts) if len(pay_amounts) > 1 else 0.0
    data['recent_payment_amount'] = pay_amounts[0]
    data['recent_bill_amount'] = bill_amounts[0]
    
    # recent_payment_ratio: 0 if denominator <= 0, capped between 0 and 5
    if data['recent_bill_amount'] > 0:
        val_rpr = data['recent_payment_amount'] / data['recent_bill_amount']
    else:
        val_rpr = 0.0
    data['recent_payment_ratio'] = max(0.0, min(5.0, val_rpr))
        
    return data

from fastapi.middleware.cors import CORSMiddleware

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/recovery/analyze", response_model=FinalRecoveryPlan)
def analyze_recovery(request: RecoveryAnalysisRequest, db: Session = Depends(get_db)) -> FinalRecoveryPlan:
    """Validate customer data and return the pipeline's validated recovery plan."""
    request_data = request.model_dump()
    customer_id = request_data.pop("customer_id")
    
    # Compute derived features
    full_data = compute_derived_features(request_data)
    
    try:
        plan = run_recovery_pipeline(
            customer_data=full_data,
            customer_id=customer_id,
        )
        
        # Upsert Customer
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            customer = Customer(customer_id=customer_id)
            db.add(customer)
        
        # Update customer fields
        customer.nickname = request_data.get("nickname")
        for key, value in full_data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
                
        # REVIEW: amount_at_risk Interpretation
        # Here we use the full recent bill (bill_amount_1) as the financial exposure (amount_at_risk)
        # rather than Expected Loss (bill_amount_1 * failure_probability). 
        # Rationale: "Revenue at Risk" in typical collections dashboards reflects the total 
        # nominal value of invoices at risk of default. Using Expected Loss would dilute 
        # the metric's visibility and misrepresent the actual dollars the agent is trying to recover.
        amount_at_risk = max(0.0, float(customer.bill_amount_1 or 0.0))
        
        db_case = RecoveryCase(
            customer_id=customer_id,
            failure_probability=plan.failure_probability,
            predicted_failure=plan.predicted_failure,
            risk_level=plan.risk_level,
            priority=plan.priority,
            strategy=plan.strategy,
            communication_channel=plan.communication_channel,
            follow_up_days=plan.follow_up_days,
            escalation_candidate=plan.escalation_candidate,
            final_action=plan.final_action,
            customer_message=plan.customer_message,
            follow_up_action=plan.follow_up_action,
            status="Proactive" if plan.priority == "PROACTIVE" else "Pending",
            amount_at_risk=amount_at_risk,
            recovery_status="Pending",
            max_attempts=MAX_RECOVERY_ATTEMPTS,
            attempt_count=0
        )
        db.add(db_case)
        db.commit()
        
        return plan
        
    except CrewAIWorkflowError as exc:
        raise HTTPException(
            status_code=502,
            detail="Recovery communication service is unavailable.",
        ) from exc
    except JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Recovery communication service returned an invalid response.",
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Recovery plan validation failed.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail="Recovery plan validation failed.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the recovery analysis.",
        ) from exc

@app.get("/customers")
def get_customers(search: str = None, db: Session = Depends(get_db)):
    query = db.query(Customer)
    if search:
        query = query.filter(Customer.customer_id.cast(String).contains(search))
    customers = query.order_by(Customer.updated_at.desc()).all()
    
    results = []
    for c in customers:
        latest_case = db.query(RecoveryCase).filter(RecoveryCase.customer_id == c.customer_id).order_by(RecoveryCase.created_at.desc()).first()
        results.append({
            "id": c.id,
            "customer_id": c.customer_id,
            "nickname": c.nickname,
            "credit_limit": c.credit_limit,
            "risk": latest_case.risk_level if latest_case else "UNKNOWN",
            "status": latest_case.status if latest_case else "Active",
            "updated_at": c.updated_at
        })
    return results

@app.get("/customers/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    latest_case = db.query(RecoveryCase).filter(RecoveryCase.customer_id == customer_id).order_by(RecoveryCase.created_at.desc()).first()
    cases = db.query(RecoveryCase).filter(RecoveryCase.customer_id == customer_id).order_by(RecoveryCase.created_at.desc()).all()
    
    return {
        "customer": {c.name: getattr(customer, c.name) for c in customer.__table__.columns},
        "latest_case": {c.name: getattr(latest_case, c.name) for c in latest_case.__table__.columns} if latest_case else None,
        "history": [{c.name: getattr(case, c.name) for c in case.__table__.columns} for case in cases]
    }

@app.get("/recovery/cases")
def get_cases(search: str = None, risk: str = None, strategy: str = None, channel: str = None, status: str = None, priority: str = None, db: Session = Depends(get_db)):
    query = db.query(RecoveryCase)
    if search:
        query = query.filter(RecoveryCase.customer_id.cast(String).contains(search))
    if risk and risk != "All":
        query = query.filter(RecoveryCase.risk_level == risk)
    if strategy and strategy != "All":
        query = query.filter(RecoveryCase.strategy == strategy)
    if channel and channel != "All":
        query = query.filter(RecoveryCase.communication_channel == channel)
    if status and status != "All":
        query = query.filter(RecoveryCase.status == status)
    else:
        # Exclude completed cases by default in active case views
        query = query.filter(RecoveryCase.status != "Completed")
    if priority and priority != "All":
        query = query.filter(RecoveryCase.priority_tier == priority)
        
    cases = query.order_by(RecoveryCase.created_at.desc()).all()
    results = []
    for case in cases:
        case_dict = {c.name: getattr(case, c.name) for c in case.__table__.columns}
        case_dict["nickname"] = case.customer.nickname if case.customer else None
        results.append(case_dict)
    return results

from pydantic import BaseModel
import datetime

from typing import Literal

class RecoveryOutcomeRequest(BaseModel):
    amount_recovered: float
    recovery_status: Literal["Pending", "In Progress", "Recovered", "Partially Recovered", "Failed", "Escalated"]

@app.put("/recovery/cases/{case_id}/outcome")
def update_outcome(case_id: int, outcome: RecoveryOutcomeRequest, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if outcome.amount_recovered < 0:
        raise HTTPException(status_code=400, detail="Recovered amount cannot be negative")
        
    if case.amount_at_risk < 0:
        raise HTTPException(status_code=400, detail="Amount at risk cannot be negative")
        
    if outcome.amount_recovered > case.amount_at_risk:
        raise HTTPException(status_code=400, detail="Recovered amount cannot exceed the amount at risk")
    
    case.amount_recovered = outcome.amount_recovered
    case.recovery_status = outcome.recovery_status
    
    if case.amount_recovered >= case.amount_at_risk and case.amount_at_risk > 0:
        if case.status == "Escalated":
            case.status = "Pending"  # De-escalate if fully recovered
            case.escalation_reason = None
            
    if outcome.recovery_status in ["Recovered", "Partially Recovered", "Failed", "Escalated"]:
        case.recovery_completed_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Outcome updated"}


@app.post("/recovery/analyze-batch")
def analyze_recovery_batch(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    
    results = []
    max_amount_at_risk_in_batch = 0.0
    errors = []
    
    for customer in customers:
        try:
            cust_dict = {c.name: getattr(customer, c.name) for c in customer.__table__.columns}
            # Add customer_id manually to dict to be safe if compute_derived_features or pipeline needs it
            full_data = compute_derived_features(cust_dict)
            
            from ml.predict import predict_payment_failure
            from crew.rules.recovery_rules import determine_recovery_policy
            
            risk = predict_payment_failure(full_data, customer.customer_id)
            recovery_policy = determine_recovery_policy(
                risk_level=risk.risk_level,
                predicted_failure=risk.predicted_failure,
                num_delayed_payments=risk.num_delayed_payments,
                recent_payment_ratio=risk.recent_payment_ratio,
                payment_to_bill_ratio=risk.payment_to_bill_ratio,
            )
            
            amount_at_risk = max(0.0, float(customer.bill_amount_1 or 0.0))
            if amount_at_risk > max_amount_at_risk_in_batch:
                max_amount_at_risk_in_batch = amount_at_risk
                
            results.append({
                "customer": customer,
                "risk": risk,
                "recovery_policy": recovery_policy,
                "amount_at_risk": amount_at_risk
            })
        except Exception as e:
            errors.append({"customer_id": customer.customer_id, "error": str(e)})

    new_cases_created = 0
    existing_cases_updated = 0
    cases_skipped = 0
    tiers_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    
    from api.services.scoring import calculate_priority_score, update_active_case_analytics

    for res in results:
        customer = res["customer"]
        risk = res["risk"]
        recovery_policy = res["recovery_policy"]
        amount_at_risk = res["amount_at_risk"]
        
        # Check active case
        # Active definition: status != "Completed" AND amount_recovered < amount_at_risk
        active_cases = [c for c in customer.cases if c.status != "Completed" and c.amount_recovered < c.amount_at_risk]
        
        # Select the most recent active case if multiple exist
        active_case = sorted(active_cases, key=lambda c: c.id, reverse=True)[0] if active_cases else None
        
        if active_case:
            priority_dict = calculate_priority_score(
                failure_probability=risk.failure_probability,
                amount_at_risk=amount_at_risk,
                max_amount_in_batch=max_amount_at_risk_in_batch,
                attempt_count=active_case.attempt_count,
                status=active_case.status
            )
            
            new_analytics = {
                "failure_probability": risk.failure_probability,
                "predicted_failure": risk.predicted_failure,
                "risk_level": risk.risk_level,
                "priority": recovery_policy.priority,
                "priority_score": priority_dict["priority_score"],
                "priority_tier": priority_dict["priority_tier"],
                "priority_factors": priority_dict["priority_factors"],
                "amount_at_risk": amount_at_risk
            }
            
            update_active_case_analytics(active_case, new_analytics)
            existing_cases_updated += 1
            tiers_count[priority_dict["priority_tier"]] += 1
            
        else:
            # Create a new RecoveryCase
            priority_dict = calculate_priority_score(
                failure_probability=risk.failure_probability,
                amount_at_risk=amount_at_risk,
                max_amount_in_batch=max_amount_at_risk_in_batch,
                attempt_count=0,
                status="Proactive" if recovery_policy.priority == "PROACTIVE" else "Pending"
            )
            
            db_case = RecoveryCase(
                customer_id=customer.customer_id,
                failure_probability=risk.failure_probability,
                predicted_failure=risk.predicted_failure,
                risk_level=risk.risk_level,
                priority=recovery_policy.priority,
                strategy=recovery_policy.strategy,
                communication_channel=recovery_policy.communication_channel,
                follow_up_days=recovery_policy.follow_up_days,
                escalation_candidate=recovery_policy.escalation_candidate,
                final_action="",
                customer_message="",
                follow_up_action="",
                status="Proactive" if recovery_policy.priority == "PROACTIVE" else "Pending",
                amount_at_risk=amount_at_risk,
                recovery_status="Pending",
                max_attempts=MAX_RECOVERY_ATTEMPTS,
                attempt_count=0,
                priority_score=priority_dict["priority_score"],
                priority_tier=priority_dict["priority_tier"],
                priority_factors=priority_dict["priority_factors"]
            )
            db.add(db_case)
            new_cases_created += 1
            tiers_count[priority_dict["priority_tier"]] += 1
            
    db.commit()
    
    return {
        "success": True,
        "total_analyzed": len(results),
        "new_cases_created": new_cases_created,
        "existing_cases_updated": existing_cases_updated,
        "cases_skipped": cases_skipped,
        "critical_cases": tiers_count["CRITICAL"],
        "high_priority_cases": tiers_count["HIGH"],
        "medium_priority_cases": tiers_count["MEDIUM"],
        "low_priority_cases": tiers_count["LOW"],
        "errors": errors
    }

@app.post("/recovery/cases/{case_id}/generate-action")
def generate_ai_action(case_id: int, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # HARD STOPPING RULES (Backend enforced)
    def save_hard_rule(decision, reason, recommended_action):
        case.ai_decision = decision
        case.ai_reasoning = reason
        case.ai_recommended_action = recommended_action
        case.ai_confidence = 1.0
        case.ai_communication_channel = None
        case.ai_follow_up_days = None
        case.ai_customer_message = None
        db.commit()
        return {
            "success": True,
            "ai_decision": case.ai_decision,
            "ai_reasoning": case.ai_reasoning,
            "ai_recommended_action": case.ai_recommended_action,
            "ai_confidence": case.ai_confidence
        }

    if case.amount_recovered >= case.amount_at_risk:
        return save_hard_rule("STOP", "Recovery target has already been reached.", "Stop Recovery")
    
    if case.status == "Completed":
        return save_hard_rule("STOP", "Case is already completed.", "Stop Recovery")
        
    if case.status == "Escalated":
        return save_hard_rule("STOP", "Case is already escalated.", "Stop Recovery")
        
    if case.attempt_count >= case.max_attempts:
        return save_hard_rule("ESCALATE", "Maximum recovery attempts reached.", "Escalate Case")
        
    customer = case.customer
    case_dict = {c.name: getattr(case, c.name) for c in case.__table__.columns}
    cust_dict = {c.name: getattr(customer, c.name) for c in customer.__table__.columns} if customer else {}
    
    from api.services.recovery_ai import generate_ai_action_internal
    
    try:
        ai_response = generate_ai_action_internal(case_dict, cust_dict)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    decision = ai_response.get("decision")
    if decision not in ["STOP", "CONTINUE", "ESCALATE"]:
        raise HTTPException(status_code=500, detail="Invalid decision from AI.")
        
    case.ai_decision = decision
    case.ai_recommended_action = ai_response.get("recommended_action")
    case.ai_reasoning = ai_response.get("reason")
    case.ai_confidence = ai_response.get("confidence")
    case.ai_communication_channel = ai_response.get("communication_channel")
    case.ai_follow_up_days = ai_response.get("follow_up_days")
    case.ai_customer_message = ai_response.get("customer_message")
    
    db.commit()
    
    return {
        "success": True,
        "ai_decision": case.ai_decision,
        "ai_recommended_action": case.ai_recommended_action,
        "ai_reasoning": case.ai_reasoning,
        "ai_confidence": case.ai_confidence,
        "ai_communication_channel": case.ai_communication_channel,
        "ai_follow_up_days": case.ai_follow_up_days,
        "ai_customer_message": case.ai_customer_message
    }

@app.post("/recovery/cases/{case_id}/attempt")
def record_attempt(case_id: int, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    return process_recovery_attempt(case, db, commit=True)

@app.put("/recovery/cases/{case_id}/complete")
def complete_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.status = "Completed"
    db.commit()
    return {"status": "success", "message": "Case marked as completed"}

@app.get("/recovery/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    customer = db.query(Customer).filter(Customer.customer_id == case.customer_id).first()
    return {
        "case": {c.name: getattr(case, c.name) for c in case.__table__.columns},
        "customer": {c.name: getattr(customer, c.name) for c in customer.__table__.columns} if customer else None
    }

@app.get("/dashboard/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_analyzed = db.query(func.count(Customer.id)).scalar() or 0
    high_risk = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.risk_level == "HIGH").scalar() or 0
    proactive = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.status == "Proactive").scalar() or 0
    escalated = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.status == "Escalated").scalar() or 0
    
    return {
        "total_analyzed": total_analyzed,
        "high_risk": high_risk,
        "proactive": proactive,
        "escalated": escalated
    }

@app.get("/analytics/metrics")
def get_analytics_metrics(db: Session = Depends(get_db)):
    risk_dist = db.query(RecoveryCase.risk_level, func.count(RecoveryCase.id)).group_by(RecoveryCase.risk_level).all()
    strategy_dist = db.query(RecoveryCase.strategy, func.count(RecoveryCase.id)).group_by(RecoveryCase.strategy).all()
    channel_dist = db.query(RecoveryCase.communication_channel, func.count(RecoveryCase.id)).group_by(RecoveryCase.communication_channel).all()
    
    # REVIEW: Case Semantics and Double Counting
    # Financial recovery is measured strictly at the RecoveryCase level. 
    # If a customer is analyzed twice, two distinct cases are created. 
    # By summing amount_at_risk and amount_recovered across ALL cases, we measure 
    # the total financial throughput of the recovery team's workflows.
    # This is internally consistent: a duplicate case means the team worked the case twice, 
    # so both the risk handled and the outcome achieved belong to the workflow metrics.
    total_cases = db.query(func.count(RecoveryCase.id)).scalar() or 0
    total_at_risk = db.query(func.sum(RecoveryCase.amount_at_risk)).scalar() or 0.0
    total_recovered = db.query(func.sum(RecoveryCase.amount_recovered)).scalar() or 0.0
    
    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0.0
    
    recovered_cases = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.recovery_status == 'Recovered').scalar() or 0
    partially_recovered_cases = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.recovery_status == 'Partially Recovered').scalar() or 0
    failed_cases = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.recovery_status == 'Failed').scalar() or 0
    escalated_cases = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.status == 'Escalated').scalar() or 0
    
    return {
        "risk_distribution": [{"name": r[0], "value": r[1]} for r in risk_dist],
        "strategy_distribution": [{"name": s[0], "value": s[1]} for s in strategy_dist],
        "channel_distribution": [{"name": c[0], "value": c[1]} for c in channel_dist],
        "total_cases": total_cases,
        "total_amount_at_risk": total_at_risk,
        "total_amount_recovered": total_recovered,
        "recovery_rate": recovery_rate,
        "recovered_cases": recovered_cases,
        "partially_recovered_cases": partially_recovered_cases,
        "failed_cases": failed_cases,
        "escalated_cases": escalated_cases
    }

from api.services.recovery_orchestrator import evaluate_recovery_case, orchestrate_active_cases

@app.post("/recovery/cases/{case_id}/orchestrate")
def api_orchestrate_single_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    customer = db.query(Customer).filter(Customer.customer_id == case.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    try:
        result = evaluate_recovery_case(case, customer, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recovery/orchestrate")
def api_orchestrate_all_cases(db: Session = Depends(get_db)):
    try:
        stats = orchestrate_active_cases(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from api.services.recovery_action_planner import plan_recovery_action, plan_pending_recovery_actions

@app.post("/recovery/cases/{case_id}/plan-action")
def api_plan_action_single_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    try:
        action = plan_recovery_action(case, case.ai_decision, db)
        return {
            "success": True,
            "case_id": case.id,
            "action": action
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from api.services.action_executor import execute_recovery_action

@app.post("/recovery/actions/{action_id}/execute")
def api_execute_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(RecoveryAction).filter(RecoveryAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    result = execute_recovery_action(action, db)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.get("/recovery/actions/{action_id}/executions")
def api_get_action_executions(action_id: int, db: Session = Depends(get_db)):
    action = db.query(RecoveryAction).filter(RecoveryAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    executions = db.query(ExecutionAttempt).filter(ExecutionAttempt.action_id == action_id).order_by(ExecutionAttempt.attempted_at.asc()).all()
    
    result = []
    import json
    for ex in executions:
        result.append({
            "id": ex.id,
            "attempted_at": ex.attempted_at.isoformat() if ex.attempted_at else None,
            "execution_status": ex.execution_status,
            "result": ex.result,
            "error": ex.error,
            "channel": ex.channel,
            "provider": ex.provider,
            "recipient": ex.recipient,
            "metadata": json.loads(ex.metadata_payload) if ex.metadata_payload else None
        })
        
    return {
        "action_id": action_id,
        "executions": result
    }


@app.post("/recovery/cases/{case_id}/run-cycle")
def api_run_recovery_cycle(case_id: int, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    customer = case.customer
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found for case")
        
    # 1. Orchestration
    try:
        orchestration_result = evaluate_recovery_case(case, customer, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")
        
    decision = orchestration_result.get("decision")
    source = orchestration_result.get("source", "unknown")
    
    # 2. Planning
    try:
        action_dict = plan_recovery_action(case, decision, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action planning failed: {str(e)}")
        
    action_id = action_dict["id"]
    action_obj = db.query(RecoveryAction).filter(RecoveryAction.id == action_id).first()
    
    # 3. Execution
    initial_attempt_count = case.attempt_count
    try:
        exec_response = execute_recovery_action(action_obj, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
        
    # 4. Result collection
    db.refresh(case)
    attempt_recorded = case.attempt_count > initial_attempt_count
    
    attempt = db.query(ExecutionAttempt).filter_by(action_id=action_id).order_by(ExecutionAttempt.id.desc()).first()
    exec_status = attempt.execution_status if attempt else "SKIPPED"
    
    return {
        "success": True,
        "case_id": case.id,
        "orchestration": {
            "decision": decision,
            "source": source
        },
        "action": {
            "id": action_obj.id,
            "action_type": action_obj.action_type,
            "decision": action_obj.decision,
            "channel": action_obj.channel,
            "status": action_obj.status
        },
        "execution": {
            "status": exec_status,
            "provider": exec_response.get("provider") if exec_status != "SKIPPED" else None
        },
        "recovery_attempt": {
            "recorded": attempt_recorded,
            "attempt_count": case.attempt_count
        }
    }


@app.post("/recovery/cases/{case_id}/reevaluate")
def api_reevaluate_recovery_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    customer = case.customer
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found for case")
        
    try:
        res = evaluate_recovery_case(case, customer, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-evaluation failed: {str(e)}")
        
    return {
        "success": True,
        "case_id": case.id,
        "decision": res.get("decision"),
        "source": res.get("source"),
        "reason": res.get("reason"),
        "recommended_action": res.get("recommended_action"),
        "confidence": res.get("confidence"),
        "action_planned": False,
        "action_executed": False
    }


@app.post("/recovery/cases/{case_id}/run-autonomous")
def api_run_autonomous_recovery(case_id: int, max_cycles: int = 1, db: Session = Depends(get_db)):
    # 1. Clamp max_cycles safely between 1 and 5
    max_cycles = max(1, min(max_cycles, 5))
    
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    customer = case.customer
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found for case")
        
    cycles_completed = 0
    stop_reason = "MAX_CYCLES_REACHED"
    final_decision = None
    actions_list = []
    
    while cycles_completed < max_cycles:
        # Re-fetch case state continuously
        db.refresh(case)
        
        # Phase 1: Orchestrate (includes all deterministic constraints internally)
        try:
            orch = evaluate_recovery_case(case, customer, db)
        except Exception as e:
            stop_reason = f"ORCHESTRATION_ERROR: {str(e)}"
            break
            
        decision = orch.get("decision")
        source = orch.get("source")
        final_decision = decision
        
        # Phase 2: Plan
        try:
            action_dict = plan_recovery_action(case, decision, db)
        except Exception as e:
            stop_reason = f"PLANNING_ERROR: {str(e)}"
            break
            
        action_obj = db.query(RecoveryAction).filter(RecoveryAction.id == action_dict["id"]).first()
        
        # Phase 3: Execute (includes attempt persistence)
        initial_attempts = case.attempt_count
        try:
            exec_response = execute_recovery_action(action_obj, db)
        except Exception as e:
            stop_reason = f"EXECUTION_ERROR: {str(e)}"
            break
            
        db.refresh(case)
        attempt_recorded = case.attempt_count > initial_attempts
        attempt = db.query(ExecutionAttempt).filter_by(action_id=action_obj.id).order_by(ExecutionAttempt.id.desc()).first()
        exec_status = attempt.execution_status if attempt else "SKIPPED"
        
        # Phase 4: Track
        actions_list.append({
            "cycle": cycles_completed + 1,
            "decision": decision,
            "action_id": action_obj.id,
            "action_type": action_obj.action_type,
            "channel": action_obj.channel,
            "execution_status": exec_status,
            "attempt_recorded": attempt_recorded,
            "attempt_count": case.attempt_count
        })
        
        cycles_completed += 1
        
        # Phase 5: Re-evaluate and determine loop termination boundaries
        if exec_status == "FAILED":
            stop_reason = "EXECUTION_FAILED"
            break
        elif exec_status == "BLOCKED":
            stop_reason = "EXECUTION_BLOCKED"
            break
        elif exec_status == "SKIPPED":
            if decision == "ESCALATE" or action_obj.action_type == "ESCALATION_REVIEW":
                stop_reason = "ESCALATION_REQUIRED"
            elif decision == "STOP" or action_obj.action_type == "NO_ACTION":
                stop_reason = "DETERMINISTIC_STOP" if source == "deterministic_rule" else "ORCHESTRATOR_STOP"
            else:
                stop_reason = "EXECUTION_SKIPPED"
            break
            
        if cycles_completed >= max_cycles:
            stop_reason = "MAX_CYCLES_REACHED"
            break
            
    return {
        "success": True,
        "case_id": case.id,
        "cycles_requested": max_cycles,
        "cycles_completed": cycles_completed,
        "stop_reason": stop_reason,
        "final_decision": final_decision,
        "final_attempt_count": case.attempt_count,
        "actions": actions_list
    }
