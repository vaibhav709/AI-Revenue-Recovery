"""FastAPI integration for the payment recovery pipeline."""

from fastapi import FastAPI

from api.schemas import RecoveryAnalysisRequest
from crew.pipeline import run_recovery_pipeline
from crew.rules.recovery_schema import FinalRecoveryPlan


app = FastAPI()


@app.post("/recovery/analyze", response_model=FinalRecoveryPlan)
def analyze_recovery(request: RecoveryAnalysisRequest) -> FinalRecoveryPlan:
    """Validate customer data and return the pipeline's validated recovery plan."""
    request_data = request.model_dump()
    customer_id = request_data.pop("customer_id")
    return run_recovery_pipeline(customer_data=request_data, customer_id=customer_id)
