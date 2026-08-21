"""FastAPI integration for the payment recovery pipeline."""

from json import JSONDecodeError

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from api.schemas import RecoveryAnalysisRequest
from crew.pipeline import CrewAIWorkflowError, run_recovery_pipeline
from crew.rules.recovery_schema import FinalRecoveryPlan


app = FastAPI()


@app.post("/recovery/analyze", response_model=FinalRecoveryPlan)
def analyze_recovery(request: RecoveryAnalysisRequest) -> FinalRecoveryPlan:
    """Validate customer data and return the pipeline's validated recovery plan."""
    request_data = request.model_dump()
    customer_id = request_data.pop("customer_id")
    try:
        return run_recovery_pipeline(
            customer_data=request_data,
            customer_id=customer_id,
        )
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
