from crewai import Task

from crew.agents import (
    risk_analyst,
    strategy_agent,
    recovery_agent,
)


# --------------------------------------------------
# TASK 1 — RISK ANALYSIS
# --------------------------------------------------

risk_analysis_task = Task(
    description="""
    Analyze the customer's payment risk.

    Customer information:
    {customer_data}

    The machine learning model has already calculated:

    - failure probability
    - predicted failure
    - risk level

    These ML values are authoritative.

    DO NOT:
    - make a new prediction
    - change any ML values
    - invent financial information

    Analyze only the information supplied.

    Identify:

    1. The strongest risk factors.
    2. The customer's payment behavior.
    3. Any warning signs.
    4. An overall risk assessment.

    Your role is analysis only.
    You do not make recovery-policy decisions.
    """,

    expected_output="""
    A concise risk assessment containing:

    - Failure probability
    - Predicted failure
    - Risk level
    - Key risk factors
    - Payment behavior analysis
    - Warning signs
    - Overall risk assessment

    Do not modify the ML prediction.
    Do not create recovery-policy decisions.
    """,

    agent=risk_analyst,
)


# --------------------------------------------------
# TASK 2 — RECOVERY STRATEGY EXPLANATION
# --------------------------------------------------

strategy_task = Task(
    description="""
    Explain and operationalize the deterministic recovery policy
    supplied by the Python business-rules engine.

    Customer information:
    {customer_data}

    Risk analysis:
    {risk_analysis}

    Deterministic recovery policy:
    {recovery_policy}

    IMPORTANT:

    The deterministic recovery policy is authoritative.

    Python has already decided:

    - recovery priority
    - recovery strategy
    - communication channel
    - follow-up timing
    - escalation status

    You have NO authority to change these decisions.

    You MUST NOT:

    - change the recovery priority
    - change the recovery strategy
    - change the communication channel
    - change the follow-up timing
    - change the escalation decision
    - create new business rules
    - create a new ML prediction
    - recommend a different strategy
    - recommend a different communication channel
    - recommend a different follow-up period
    - invent financial information

    Your job is explanation, not decision-making.

    Explain:

    1. Why the supplied strategy is appropriate.
    2. How the supplied communication channel should be used.
    3. How the supplied follow-up timing should be applied.
    4. Why the supplied escalation status is appropriate,
       without changing it.

    Only use information supplied in the customer data,
    risk analysis, and deterministic recovery policy.
    """,

    expected_output="""
    A concise explanation containing:

    - Supplied recovery priority
    - Supplied recovery strategy
    - Supplied communication channel
    - Supplied follow-up timing
    - Supplied escalation status
    - Why the supplied strategy is appropriate
    - How the supplied communication should be handled
    - How the supplied follow-up timing should be applied
    - Explanation of the supplied escalation status

    Do not introduce or recommend alternative business decisions.
    """,

    agent=strategy_agent,
)


# --------------------------------------------------
# TASK 3 — FINAL RECOVERY COMMUNICATION
# --------------------------------------------------

recovery_task = Task(
    description="""
    Create the final customer-facing recovery communication
    and operational explanation.

    Customer information:
    {customer_data}

    Risk analysis:
    {risk_analysis}

    Deterministic recovery policy:
    {recovery_policy}

    IMPORTANT:

    The deterministic recovery policy is authoritative.

    Python has already decided:

    Priority:
    {recovery_priority}

    Strategy:
    {recovery_strategy}

    Communication channel:
    {communication_channel}

    Follow-up:
    {follow_up_days} days

    Escalation candidate:
    {escalation_candidate}

    You have NO authority to change any of these values.

    DO NOT:

    - change the recovery priority
    - change the recovery strategy
    - change the communication channel
    - change the follow-up timing
    - change escalation_candidate
    - create escalation conditions
    - create new business rules
    - create a new ML prediction
    - recommend a different recovery strategy
    - recommend a different communication channel
    - recommend a different follow-up period
    - invent financial information
    - invent an outstanding balance
    - invent a due date
    - invent payment terms
    - invent discounts
    - invent penalties
    - invent fees

    The Python rules engine owns all business decisions.

    Your responsibility is ONLY to:

    1. Explain the supplied recovery action.
    2. Create the customer-facing message.
    3. Explain how the supplied follow-up should be communicated.
    4. Explain the supplied policy in professional language.

    FINANCIAL DATA SAFETY:

    Only use financial values explicitly supplied in customer_data.

    Do NOT calculate or infer an outstanding balance.

    Do NOT assume that a payment was applied entirely to a
    particular bill unless the data explicitly confirms this.

    Do NOT claim that the customer owes a specific amount unless
    that amount is explicitly provided.

    If information is unavailable, explicitly state:

    "This information must be confirmed."

    ESCALATION:

    Do not create, modify, or recommend escalation conditions.

    The escalation decision has already been made by Python.

    The final output from this task must contain ONLY:

    - final_action
    - customer_message
    - follow_up_action

    Python will add the authoritative policy fields afterward.
    """,

    expected_output="""
    Return ONLY valid JSON matching this exact structure:

    {
        "final_action": "string",
        "customer_message": "string",
        "follow_up_action": "string"
    }

    Rules:

    - Do not include customer_id.
    - Do not include priority.
    - Do not include strategy.
    - Do not include communication_channel.
    - Do not include follow_up_days.
    - Do not include escalation_candidate.
    - Do not include escalation conditions.
    - Do not add extra fields.
    - Do not invent financial information.
    - Do not invent balances, due dates, penalties, discounts, fees,
      or payment terms.
    - If information is unavailable, state:
      "This information must be confirmed."
    - Return JSON only.
    """,

    agent=recovery_agent,

    context=[
        risk_analysis_task,
        strategy_task,
    ],
)