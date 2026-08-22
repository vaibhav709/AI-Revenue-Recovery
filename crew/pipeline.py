"""Reusable, policy-controlled payment recovery pipeline."""

import json
from collections.abc import Mapping
from typing import Any

from crew.rules.recovery_rules import (
    determine_escalation_conditions,
    determine_recovery_policy,
)
from crew.rules.recovery_schema import FinalRecoveryPlan, validate_final_plan
from ml.predict import predict_payment_failure


class CrewAIWorkflowError(RuntimeError):
    """Raised when the CrewAI workflow cannot produce a response."""


def _build_customer_context(risk: Any) -> dict[str, Any]:
    """Prepare the ML-owned data supplied to the CrewAI workflow."""
    return {
        "customer_id": risk.customer_id,
        "failure_probability": risk.failure_probability,
        "predicted_failure": risk.predicted_failure,
        "risk_level": risk.risk_level,
        "num_delayed_payments": risk.num_delayed_payments,
        "max_payment_delay": risk.max_payment_delay,
        "avg_payment_delay": risk.avg_payment_delay,
        "recent_payment_delay": risk.recent_payment_delay,
        "credit_utilization": risk.credit_utilization,
        "payment_to_bill_ratio": risk.payment_to_bill_ratio,
        "recent_payment_ratio": risk.recent_payment_ratio,
        "recent_payment_amount": risk.recent_payment_amount,
        "recent_bill_amount": risk.recent_bill_amount,
    }


def _run_crewai_workflow(inputs: dict[str, Any]) -> str:
    """Run the existing sequential three-agent workflow and return its raw JSON."""
    # These imports stay inside the workflow boundary so ML and policy-only
    # callers do not initialize the CrewAI runtime.
    from crew.agents import recovery_agent, risk_analyst, strategy_agent
    from crew.tasks import recovery_task, risk_analysis_task, strategy_task
    from crewai import Crew, Process

    recovery_crew = Crew(
        agents=[risk_analyst, strategy_agent, recovery_agent],
        tasks=[risk_analysis_task, strategy_task, recovery_task],
        process=Process.sequential,
        verbose=True,
    )
    return recovery_crew.kickoff(inputs=inputs).raw


def run_recovery_pipeline(
    customer_data: Mapping[str, Any], customer_id: int
) -> FinalRecoveryPlan:
    """Run ML, deterministic policy, CrewAI communication, and final validation.

    Python owns the customer ID and every policy field.  The CrewAI workflow
    supplies only the three communication fields that are copied into the
    returned, validated ``FinalRecoveryPlan``.
    """
    risk = predict_payment_failure(customer_data, customer_id)
    customer_context = _build_customer_context(risk)

    recovery_policy = determine_recovery_policy(
        risk_level=risk.risk_level,
        predicted_failure=risk.predicted_failure,
        num_delayed_payments=risk.num_delayed_payments,
        recent_payment_ratio=risk.recent_payment_ratio,
        payment_to_bill_ratio=risk.payment_to_bill_ratio,
    )

    # Execute the authoritative escalation rules even though the resulting
    # conditions are explanatory data, not LLM input or LLM-owned output.
    determine_escalation_conditions(
        policy=recovery_policy,
        risk_level=risk.risk_level,
        predicted_failure=risk.predicted_failure,
        num_delayed_payments=risk.num_delayed_payments,
    )

    try:
        llm_output = _run_crewai_workflow(
            {
                "customer_data": customer_context,
                "recovery_policy": recovery_policy.model_dump(),
                "recovery_priority": recovery_policy.priority,
                "recovery_strategy": recovery_policy.strategy,
                "communication_channel": recovery_policy.communication_channel,
                "follow_up_days": recovery_policy.follow_up_days,
                "escalation_candidate": recovery_policy.escalation_candidate,
                # The task context supplies the actual preceding task output.
                "risk_analysis": "See the Risk Analyst task output in the task context.",
            }
        )
    except Exception as exc:
        raise CrewAIWorkflowError("CrewAI workflow failed.") from exc
    llm_data = json.loads(llm_output)

    # Do not merge llm_data here: that would allow an LLM-supplied policy key
    # to replace a Python-owned decision.
    final_plan = FinalRecoveryPlan.model_validate(
        {
            "customer_id": risk.customer_id,
            "failure_probability": risk.failure_probability,
            "predicted_failure": risk.predicted_failure,
            "risk_level": risk.risk_level,
            "credit_utilization": risk.credit_utilization,
            "payment_to_bill_ratio": risk.payment_to_bill_ratio,
            "priority": recovery_policy.priority,
            "strategy": recovery_policy.strategy,
            "communication_channel": recovery_policy.communication_channel,
            "follow_up_days": recovery_policy.follow_up_days,
            "escalation_candidate": recovery_policy.escalation_candidate,
            "final_action": llm_data["final_action"],
            "customer_message": llm_data["customer_message"],
            "follow_up_action": llm_data["follow_up_action"],
        }
    )
    validate_final_plan(recovery_policy, final_plan)

    if final_plan.escalation_candidate != recovery_policy.escalation_candidate:
        raise ValueError(
            "Final plan escalation decision does not match the "
            "deterministic recovery policy."
        )

    return final_plan
