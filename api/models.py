"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, unique=True, index=True)
    nickname = Column(String, nullable=True)
    
    credit_limit = Column(Integer)
    gender = Column(Integer)
    education = Column(Integer)
    marital_status = Column(Integer)
    age = Column(Integer)
    
    pay_status_1 = Column(Integer)
    pay_status_2 = Column(Integer)
    pay_status_3 = Column(Integer)
    pay_status_4 = Column(Integer)
    pay_status_5 = Column(Integer)
    pay_status_6 = Column(Integer)

    bill_amount_1 = Column(Integer)
    bill_amount_2 = Column(Integer)
    bill_amount_3 = Column(Integer)
    bill_amount_4 = Column(Integer)
    bill_amount_5 = Column(Integer)
    bill_amount_6 = Column(Integer)

    payment_amount_1 = Column(Integer)
    payment_amount_2 = Column(Integer)
    payment_amount_3 = Column(Integer)
    payment_amount_4 = Column(Integer)
    payment_amount_5 = Column(Integer)
    payment_amount_6 = Column(Integer)

    num_delayed_payments = Column(Integer)
    max_payment_delay = Column(Integer)
    avg_payment_delay = Column(Float)
    recent_payment_delay = Column(Integer)

    avg_bill_amount = Column(Float)
    avg_payment_amount = Column(Float)
    total_bill_amount = Column(Integer)
    total_payment_amount = Column(Integer)

    payment_to_bill_ratio = Column(Float)
    credit_utilization = Column(Float)
    payment_std = Column(Float)
    recent_payment_amount = Column(Integer)
    recent_bill_amount = Column(Integer)
    recent_payment_ratio = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cases = relationship("RecoveryCase", back_populates="customer", cascade="all, delete-orphan")


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    
    # ML Outputs
    failure_probability = Column(Float)
    predicted_failure = Column(Boolean)
    risk_level = Column(String)
    
    # Policy Outputs
    priority = Column(String)
    priority_score = Column(Integer, nullable=True)
    priority_tier = Column(String, nullable=True)
    priority_factors = Column(String, nullable=True)
    strategy = Column(String)
    communication_channel = Column(String)
    follow_up_days = Column(Integer)
    escalation_candidate = Column(Boolean)
    
    # AI/Final Actions
    final_action = Column(String)
    customer_message = Column(String)
    follow_up_action = Column(String)
    
    status = Column(String, default="Pending")

    # Financial Recovery
    amount_at_risk = Column(Float, default=0.0)
    amount_recovered = Column(Float, default=0.0)
    recovery_status = Column(String, default="Pending")
    recovery_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Recovery Attempt Tracking
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    last_attempt_at = Column(DateTime, nullable=True)
    escalation_reason = Column(String, nullable=True)

    # AI Recommendation
    ai_decision = Column(String, nullable=True)
    ai_recommended_action = Column(String, nullable=True)
    ai_reasoning = Column(String, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_communication_channel = Column(String, nullable=True)
    ai_follow_up_days = Column(Integer, nullable=True)
    ai_customer_message = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="cases")

MAX_RECOVERY_ATTEMPTS = 5

class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("recovery_cases.id"), index=True)
    action_type = Column(String)
    decision = Column(String)
    channel = Column(String, nullable=True)
    description = Column(String, nullable=True)
    status = Column(String, default="PENDING")
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    case = relationship("RecoveryCase", back_populates="actions")

RecoveryCase.actions = relationship("RecoveryAction", back_populates="case", cascade="all, delete-orphan")

class ExecutionAttempt(Base):
    __tablename__ = "execution_attempts"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("recovery_actions.id"), index=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    execution_status = Column(String)  # SUCCESS, FAILED, BLOCKED, SKIPPED
    result = Column(String, nullable=True)
    error = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    recipient = Column(String, nullable=True)
    metadata_payload = Column(String, nullable=True)

    action = relationship("RecoveryAction", back_populates="executions")

RecoveryAction.executions = relationship("ExecutionAttempt", back_populates="action", cascade="all, delete-orphan")
