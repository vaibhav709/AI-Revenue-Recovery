from crewai import Task

from crew.agents import risk_analyst, strategy_agent


risk_analysis_task = Task(
    description="""
    Analyze the customer's payment risk using the machine learning
    prediction and supporting payment behavior data.

    Customer information:
    {customer_data}

    The machine learning model has already calculated the failure
    probability and risk level.

    Your job is NOT to make a new prediction.

    Instead:
    1. Interpret the ML prediction.
    2. Identify the strongest factors contributing to the risk.
    3. Explain the customer's payment behavior.
    4. Give a concise risk assessment.
    """,

    expected_output="""
    A concise risk assessment containing:

    - Failure probability
    - Risk level
    - Key risk factors
    - Explanation of payment behavior
    - Overall risk assessment
    """,

    agent=risk_analyst
)


strategy_task = Task(
    description="""
    Develop a practical payment recovery strategy based on the
    customer's risk assessment.

    Customer information:
    {customer_data}

    Risk analysis:
    {risk_analysis}

    The ML model has already predicted the payment failure risk.
    Do NOT create a new ML prediction.

    Based on the risk analysis:

    1. Determine the appropriate recovery priority.
    2. Select an appropriate recovery approach.
    3. Recommend the communication channel.
    4. Recommend when the customer should be followed up.
    5. Explain why the proposed strategy is appropriate.
    6. Keep the strategy proportional to the customer's risk.

    Avoid unnecessarily aggressive recovery actions for low-risk
    customers.
    """,

    expected_output="""
    A structured payment recovery strategy containing:

    - Recovery priority
    - Recommended strategy
    - Communication channel
    - Follow-up timing
    - Reasoning behind the strategy
    """,

    agent=strategy_agent
)