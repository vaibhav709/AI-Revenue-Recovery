from ml.predict import predict_payment_failure
from crew.agents import risk_analyst, strategy_agent
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
# ML PREDICTION
# --------------------------------------------------

risk = predict_payment_failure(
    customer_data,
    customer_id=8681
)

print("\n===== ML PREDICTION =====")
print(risk)


# --------------------------------------------------
# PREPARE DATA FOR CREWAI
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

    Identify:
    1. The strongest risk factors.
    2. The customer's payment behavior.
    3. Any warning signs.
    4. An overall risk assessment.
    """,

    expected_output="""
    A concise risk assessment containing:

    - Failure probability
    - Risk level
    - Key risk factors
    - Payment behavior analysis
    - Overall risk assessment
    """,

    agent=risk_analyst
)


# --------------------------------------------------
# TASK 2 — RECOVERY STRATEGY
# --------------------------------------------------

strategy_task_test = Task(
    description=f"""
    Based on the customer's information and the Risk Analyst's
    assessment, develop an appropriate payment recovery strategy.

    Customer information:
    {customer_context}

    Do NOT create a new ML prediction.

    The strategy should include:

    1. Recovery priority.
    2. Recommended recovery approach.
    3. Communication channel.
    4. Follow-up timing.
    5. Reasoning for the chosen strategy.

    The recovery approach must be proportional to the customer's
    risk level.
    """,

    expected_output="""
    A structured recovery strategy containing:

    - Recovery priority
    - Recommended strategy
    - Communication channel
    - Follow-up timing
    - Reasoning
    """,

    agent=strategy_agent,

    context=[risk_task]
)


# --------------------------------------------------
# TWO-AGENT CREW
# --------------------------------------------------

test_crew = Crew(
    agents=[
        risk_analyst,
        strategy_agent
    ],

    tasks=[
        risk_task,
        strategy_task_test
    ],

    process=Process.sequential,

    verbose=True
)


# --------------------------------------------------
# RUN CREW
# --------------------------------------------------

result = test_crew.kickoff()

print("\n===== FINAL RECOVERY STRATEGY =====")
print(result)