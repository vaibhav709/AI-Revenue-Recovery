from ml.predict import predict_payment_failure

from crew.rules.recovery_rules import (
    determine_recovery_policy,
    determine_escalation_conditions,
)

from crew.rules.recovery_schema import (
    FinalRecoveryPlan,
    validate_final_plan,
)

from crew.agents import (
    risk_analyst,
    strategy_agent,
    recovery_agent,
)

from crewai import Crew, Process, Task


# --------------------------------------------------
# CUSTOMER DATA
# --------------------------------------------------

customer_data = {
    "credit_limit": 50000,
    "gender": 2,
    "education": 3,
    "marital_status": 1,
    "age": 43,

    "pay_status_1": 0,
    "pay_status_2": 0,
    "pay_status_3": 0,
    "pay_status_4": 0,
    "pay_status_5": 0,
    "pay_status_6": 0,

    "bill_amount_1": 39177,
    "bill_amount_2": 39607,
    "bill_amount_3": 17070,
    "bill_amount_4": 13038,
    "bill_amount_5": 8904,
    "bill_amount_6": 4740,

    "payment_amount_1": 2000,
    "payment_amount_2": 1500,
    "payment_amount_3": 3500,
    "payment_amount_4": 600,
    "payment_amount_5": 500,
    "payment_amount_6": 4000,

    "num_delayed_payments": 0,
    "max_payment_delay": 0,
    "avg_payment_delay": 0,
    "recent_payment_delay": 0,

    "avg_bill_amount": 20422.666667,
    "avg_payment_amount": 2016.666667,
    "total_bill_amount": 122536,
    "total_payment_amount": 12100,

    "payment_to_bill_ratio": 0.098746,
    "credit_utilization": 0.408453,

    "payment_std": 1463.443428,
    "recent_payment_amount": 2000,
    "recent_bill_amount": 39177,
    "recent_payment_ratio": 0.051050
}


# --------------------------------------------------
# 1. ML PREDICTION
# --------------------------------------------------

risk = predict_payment_failure(
    customer_data,
    customer_id=8681
)

print("\n===== ML PREDICTION =====")
print(risk)


# --------------------------------------------------
# 2. PREPARE DATA FOR CREWAI
# --------------------------------------------------

customer_context = {
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
    "recent_bill_amount": risk.recent_bill_amount
}


# --------------------------------------------------
# 3. DETERMINISTIC RECOVERY POLICY
# --------------------------------------------------

recovery_policy = determine_recovery_policy(
    risk_level=risk.risk_level,
    predicted_failure=risk.predicted_failure,
    num_delayed_payments=risk.num_delayed_payments,
    recent_payment_ratio=risk.recent_payment_ratio,
    payment_to_bill_ratio=risk.payment_to_bill_ratio,
)

print("\n===== DETERMINISTIC RECOVERY POLICY =====")
print(recovery_policy)

# --------------------------------------------------
# 3B. DETERMINISTIC ESCALATION CONDITIONS
# --------------------------------------------------

escalation_conditions = determine_escalation_conditions(
    policy=recovery_policy,
    risk_level=risk.risk_level,
    predicted_failure=risk.predicted_failure,
    num_delayed_payments=risk.num_delayed_payments,
)

print("\n===== DETERMINISTIC ESCALATION =====")

print(
    "Escalation candidate:",
    recovery_policy.escalation_candidate
)

print("\nTriggered escalation conditions:")

if escalation_conditions:
    for condition in escalation_conditions:
        print("-", condition)
else:
    print("- None")

# Convert Pydantic model to dictionary
policy_context = recovery_policy.model_dump()    

# --------------------------------------------------
# TASK 1 — RISK ANALYSIS
# --------------------------------------------------

risk_task = Task(
    description=f"""
    Analyze the customer's payment risk.

    Customer information:
    {customer_context}

    The ML model has already calculated the failure probability
    and risk level.

    Do NOT make a new prediction.

    Do NOT change any ML values.

    Identify:
    1. The strongest risk factors.
    2. The customer's payment behavior.
    3. Any warning signs.
    4. An overall risk assessment.

    Only use information supplied in the customer data.
    Do not invent financial facts.
    """,

    expected_output="""
    A concise risk assessment containing:

    - Failure probability
    - Risk level
    - Key risk factors
    - Payment behavior analysis
    - Warning signs
    - Overall risk assessment

    Do not modify the ML prediction.
    """,

    agent=risk_analyst
)


# --------------------------------------------------
# TASK 2 — RECOVERY STRATEGY
# --------------------------------------------------

strategy_task = Task(
    description=f"""
    Develop a payment recovery strategy for the customer.

    Customer information:
    {customer_context}

    Deterministic recovery policy:
    {policy_context}

    IMPORTANT:

    The deterministic recovery policy is authoritative.

    You MUST follow:

    Priority:
    {recovery_policy.priority}

    Strategy:
    {recovery_policy.strategy}

    Communication channel:
    {recovery_policy.communication_channel}

    Follow-up:
    {recovery_policy.follow_up_days} days

    Escalation candidate:
    {recovery_policy.escalation_candidate}

    You MUST NOT:

    - change the recovery priority
    - change the recovery strategy
    - change the communication channel
    - change the follow-up timing
    - change the escalation decision
    - create a new ML prediction
    - invent financial information
    - determine new escalation conditions
    - introduce new business rules

    Your job is to explain and operationalize the supplied policy.

    Explain:
    1. Why the supplied strategy is appropriate.
    2. How it should be communicated.
    3. How the supplied timing should be applied.
    4. Explain the supplied escalation status without changing it.
    """,

    expected_output="""
    A recovery strategy that strictly follows the deterministic policy.

    Include:

    - Recovery priority
    - Recovery strategy
    - Communication channel
    - Follow-up timing
    - Escalation status
    - Reasoning

    Do not introduce values that conflict with the policy.
    """,

    agent=strategy_agent,

    context=[risk_task]
)
# --------------------------------------------------
# TASK 3 — FINAL RECOVERY ACTION
# --------------------------------------------------

recovery_task = Task(
    description=f"""
    Create the final customer recovery communication and action plan.

    Customer information:
    {customer_context}

    Deterministic recovery policy:
    {policy_context}

    The deterministic recovery policy is authoritative.

    You are NOT responsible for deciding:

    - recovery priority
    - recovery strategy
    - communication channel
    - follow-up timing
    - escalation status
    - escalation conditions

    These values have already been determined by the
    deterministic business rules engine.

    You MUST use exactly these values:

    Priority:
    {recovery_policy.priority}

    Strategy:
    {recovery_policy.strategy}

    Communication channel:
    {recovery_policy.communication_channel}

    Follow-up:
    {recovery_policy.follow_up_days} days

    Escalation candidate:
    {recovery_policy.escalation_candidate}

    You MUST NOT:

    - change the priority
    - change the strategy
    - change the communication channel
    - change the follow-up timing
    - change escalation_candidate
    - create escalation conditions
    - create a new ML prediction
    - invent financial information
    - invent a confirmed outstanding balance
    - invent a due date
    - invent payment terms
    - invent discounts
    - invent penalties
    - invent financial information
    - recommend a different recovery strategy
    - recommend a different communication channel
    - recommend a different follow-up period
    - Do NOT assume that the recent payment amount was applied entirely or directly to the recent bill amount.
    - When mentioning payment and bill amounts together,describe them as separate recorded amounts only.
    - Do NOT imply that the payment reduced the bill by that amount.

    Your responsibility is ONLY to:

    1. Explain the supplied recovery action.
    2. Create the customer-facing message.
    3. Explain how the supplied follow-up should be communicated.
    4. Explain the supplied policy in professional language.
    
    The final response must NOT repeat or generate
    the deterministic policy fields as JSON.

    Python will construct those fields after your response.

    You are a communication and explanation layer,
    not a business decision layer.

    You have NO authority to make business decisions.

    All business decisions have already been made by Python.

    If information is unavailable, explicitly state:

    "This information must be confirmed."
    """,

expected_output="""
Return ONLY valid JSON matching this exact structure:

{
    "final_action": "string",
    "customer_message": "string",
    "follow_up_action": "string"
}

Rules:

- Do NOT include customer_id.
- Do NOT include priority.
- Do NOT include strategy.
- Do NOT include communication_channel.
- Do NOT include follow_up_days.
- Do NOT include escalation_candidate.
- Do NOT include escalation conditions.
- Do NOT make business-rule decisions.
- Do NOT recommend a different recovery strategy.
- Do NOT recommend a different communication channel.
- Do NOT recommend a different follow-up period.
- Do NOT invent financial facts.
- Do NOT invent balances.
- Do NOT invent due dates.
- Do NOT invent payment terms.
- Do NOT invent discounts.
- Do NOT invent penalties.
- Do NOT add extra fields.
- Return JSON only.
""",

    agent=recovery_agent,

    context=[
        risk_task,
        strategy_task
    ]
)
# --------------------------------------------------
# 4. THREE-AGENT CREW
# --------------------------------------------------

test_crew = Crew(
    agents=[
        risk_analyst,
        strategy_agent,
        recovery_agent
    ],

    tasks=[
        risk_task,
        strategy_task,
        recovery_task
    ],

    process=Process.sequential,

    verbose=True
)



# --------------------------------------------------
# 5. RUN CREW
# --------------------------------------------------

result = test_crew.kickoff()

print("\n===== CREW EXECUTION RESULT =====")
print(result)


# --------------------------------------------------
# 6. DETERMINISTIC ESCALATION DECISION
# --------------------------------------------------

print("\n===== DETERMINISTIC ESCALATION DECISION =====")

print(
    "Escalation candidate:",
    recovery_policy.escalation_candidate
)

print("\nEscalation conditions:")

if escalation_conditions:
    for condition in escalation_conditions:
        print("-", condition)
else:
    print("- None")


# --------------------------------------------------
# 7. FINAL POLICY VALIDATION
# --------------------------------------------------

print("\n===== FINAL POLICY VALIDATION =====")

try:

    # --------------------------------------------------
    # STEP 1 — GET LLM-GENERATED CONTENT
    # --------------------------------------------------

    llm_output = result.raw

    print("\n===== LLM GENERATED CONTENT =====")
    print(llm_output)

    # --------------------------------------------------
    # STEP 2 — PARSE LLM JSON
    # --------------------------------------------------

    import json

    llm_data = json.loads(llm_output)

    # --------------------------------------------------
    # STEP 3 — BUILD FINAL PLAN
    #
    # IMPORTANT:
    # Python owns all business-policy fields.
    # The LLM only owns communication content.
    # --------------------------------------------------

    final_plan_data = {

        # ------------------------------------------
        # PYTHON-OWNED FIELDS
        # ------------------------------------------

        "customer_id":
            risk.customer_id,

        "priority":
            recovery_policy.priority,

        "strategy":
            recovery_policy.strategy,

        "communication_channel":
            recovery_policy.communication_channel,

        "follow_up_days":
            recovery_policy.follow_up_days,

        "escalation_candidate":
            recovery_policy.escalation_candidate,

        # ------------------------------------------
        # LLM-OWNED CONTENT FIELDS
        # ------------------------------------------

        "final_action":
            llm_data["final_action"],

        "customer_message":
            llm_data["customer_message"],

        "follow_up_action":
            llm_data["follow_up_action"],
    }

    # --------------------------------------------------
    # STEP 4 — VALIDATE COMPLETE FINAL PLAN
    # --------------------------------------------------

    final_plan = FinalRecoveryPlan.model_validate(
        final_plan_data
    )

    # --------------------------------------------------
    # STEP 5 — VALIDATE AGAINST DETERMINISTIC POLICY
    # --------------------------------------------------

    validate_final_plan(
        recovery_policy,
        final_plan
    )

    print("✅ FINAL PLAN PASSED POLICY VALIDATION")

    # --------------------------------------------------
    # STEP 6 — EXPLICIT ESCALATION VALIDATION
    # --------------------------------------------------

    if (
        final_plan.escalation_candidate
        != recovery_policy.escalation_candidate
    ):
        raise ValueError(
            "Final plan escalation decision does not match "
            "the deterministic recovery policy."
        )

    print(
        "✅ ESCALATION DECISION MATCHES "
        "DETERMINISTIC POLICY"
    )

    # --------------------------------------------------
    # STEP 7 — PRINT COMPLETE FINAL PLAN
    # --------------------------------------------------

    print("\n===== COMPLETE FINAL RECOVERY PLAN =====")

    print(
        final_plan.model_dump_json(indent=2)
    )

except json.JSONDecodeError as e:

    print("❌ LLM OUTPUT IS NOT VALID JSON")
    print(e)

except KeyError as e:

    print("❌ REQUIRED LLM FIELD IS MISSING")
    print("Missing field:", e)

except Exception as e:

    print("❌ FINAL PLAN FAILED POLICY VALIDATION")
    print(e)