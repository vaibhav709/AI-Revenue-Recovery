"""FastAPI integration for the payment recovery pipeline."""
import traceback
from json import JSONDecodeError

from fastapi import FastAPI, HTTPException, Depends
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func, String

from api.schemas import RecoveryAnalysisRequest
from api.database import engine, Base, get_db
from api.models import Customer, RecoveryCase
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
                
        # Insert RecoveryCase
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
            status="Proactive" if plan.priority == "PROACTIVE" else "Escalated" if plan.priority == "HIGH" else "Pending"
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
def get_cases(search: str = None, risk: str = None, strategy: str = None, channel: str = None, status: str = None, db: Session = Depends(get_db)):
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
        
    cases = query.order_by(RecoveryCase.created_at.desc()).all()
    results = []
    for case in cases:
        case_dict = {c.name: getattr(case, c.name) for c in case.__table__.columns}
        case_dict["nickname"] = case.customer.nickname if case.customer else None
        results.append(case_dict)
    return results

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
    
    return {
        "risk_distribution": [{"name": r[0], "value": r[1]} for r in risk_dist],
        "strategy_distribution": [{"name": s[0], "value": s[1]} for s in strategy_dist],
        "channel_distribution": [{"name": c[0], "value": c[1]} for c in channel_dist]
    }
