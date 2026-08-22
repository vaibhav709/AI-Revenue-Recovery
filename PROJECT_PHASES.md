# Payment Recovery AI — Project Phases

## Completed Phases

### Phase 1 — ML Payment-Failure Prediction
Status: COMPLETE

Implemented:
- ML payment-failure prediction
- Failure probability
- Predicted failure
- Risk level
- Payment behavior features

---

### Phase 2 — Deterministic Recovery Rules
Status: COMPLETE

Implemented:
- Recovery priority
- Recovery strategy
- Communication channel
- Follow-up timing

Python rules are authoritative.

---

### Phase 3 — Deterministic Escalation Rules
Status: COMPLETE

Implemented:
- Escalation candidate
- Deterministic escalation conditions

Escalation decisions are controlled by Python.

---

### Phase 4 — CrewAI 3-Agent Workflow
Status: COMPLETE

Implemented:

ML prediction
↓
Risk Analyst
↓
Recovery Strategist
↓
Customer Recovery Specialist

CrewAI agents provide analysis and communication.

---

### Phase 5 — Policy-Controlled Final Output + Validation
Status: COMPLETE

Implemented:
- Python-owned policy fields
- LLM-generated communication fields
- Pydantic final-plan validation
- Deterministic policy validation
- Escalation consistency validation

The LLM cannot override Python-owned business decisions.

---

### Phase 6 — End-to-End Testing
Status: COMPLETE

Verified:
- ML prediction
- deterministic recovery policy
- deterministic escalation
- CrewAI execution
- final JSON generation
- final policy validation
- escalation consistency

---

# Remaining Phases

## Phase 7 — Pipeline Refactoring
Status: NEXT

Goal:

Convert the current pipeline in `testrisk.py` into a reusable function/service.

Current concept:

Customer Data
↓
ML Prediction
↓
Deterministic Recovery Rules
↓
Deterministic Escalation Rules
↓
CrewAI 3-Agent Workflow
↓
Final Policy Validation
↓
FinalRecoveryPlan

Target:

Customer Data
↓
run_recovery_pipeline()
↓
ML → Rules → CrewAI → Validation
↓
FinalRecoveryPlan

Requirements:

- Extract reusable pipeline logic from `testrisk.py`.
- Create an appropriate service/module for the pipeline.
- Accept customer data and customer ID as inputs.
- Return a validated `FinalRecoveryPlan`.
- Preserve the existing ML logic.
- Preserve deterministic recovery rules.
- Preserve deterministic escalation rules.
- Preserve the CrewAI workflow.
- Preserve final Pydantic validation.
- Preserve policy authority.
- Do not allow LLM output to override Python-owned values.
- Keep `testrisk.py` as a regression/integration test.
- Do not remove the existing end-to-end test.
- Avoid unnecessary architectural changes.

Acceptance criteria:

- `run_recovery_pipeline()` can execute the complete recovery process.
- The function returns a validated `FinalRecoveryPlan`.
- Existing `testrisk.py` continues to pass.
- The reusable pipeline produces the same business decisions as the current implementation.
- Python remains authoritative over business rules.
- No secrets are exposed.
- Relevant tests pass.

---

## Phase 8 — API Integration
Status: NOT STARTED

Expose the recovery pipeline through an API.

Example:

POST /recovery/analyze

Input:

{
    "customer_id": 8681,
    ...
}

Output:

{
    "customer_id": 8681,
    "priority": "PROACTIVE",
    "strategy": "BALANCE_CLARIFICATION",
    "communication_channel": "EMAIL",
    "follow_up_days": 5,
    "escalation_candidate": false,
    "final_action": "...",
    "customer_message": "...",
    "follow_up_action": "..."
}

The API should call the reusable recovery pipeline from Phase 7.

---

## Phase 9 — API Testing & Error Handling
Status: NOT STARTED

Test:

- valid customer
- invalid input
- missing fields
- ML failure
- CrewAI failure
- malformed LLM JSON
- policy validation failure

Expected behavior:

Bad input
↓
Controlled error

Agent failure
↓
Controlled error

Invalid plan
↓
Rejected

Valid plan
↓
Returned

---

## Phase 10 — Frontend / Dashboard Integration
Status: NOT STARTED

Connect the frontend to the recovery API.

Expected flow:

Customer Selection
↓
Analyze Risk
↓
Risk Result
↓
Recovery Strategy
↓
Recovery Message

Example dashboard:

Risk: LOW
Probability: 29.41%

Priority: PROACTIVE

Strategy:
BALANCE_CLARIFICATION

Channel: EMAIL

Follow-up: 5 days

Recovery Message:
...

---

## Phase 11 — Production Hardening
Status: NOT STARTED

Before deployment:

- environment variables
- secret protection
- logging
- API error handling
- authentication if required
- rate limiting if required
- LLM timeout handling
- retry strategy
- input validation
- security checks
- remove sensitive debug information
- production logging configuration
- appropriate CrewAI verbosity configuration

---

## Phase 12 — Final Testing & Demo
Status: NOT STARTED

Test multiple customer profiles:

LOW risk
↓
PROACTIVE recovery

MEDIUM risk
↓
STRONGER recovery

HIGH risk
↓
APPROPRIATE RECOVERY / ESCALATION

Verify:

- ML predictions remain authoritative for ML values.
- Python rules remain authoritative for business decisions.
- LLM output cannot override deterministic policy.
- Final validation rejects inconsistent plans.

---

## Phase 13 — Documentation & Deployment
Status: NOT STARTED

Prepare:

- README
- architecture diagram
- setup instructions
- API documentation
- example requests/responses
- screenshots
- deployment configuration
- final demo

---

# Architecture Principle

The final architecture must preserve:

ML Model
↓
ML Prediction

Deterministic Python Rules
↓
Business Decision

CrewAI Agents
↓
Explanation + Communication

Python / Pydantic Validation
↓
Validated FinalRecoveryPlan

The LLM must never become the authority for business decisions.

Python-owned values must remain authoritative.