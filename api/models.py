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
    strategy = Column(String)
    communication_channel = Column(String)
    follow_up_days = Column(Integer)
    escalation_candidate = Column(Boolean)
    
    # AI/Final Actions
    final_action = Column(String)
    customer_message = Column(String)
    follow_up_action = Column(String)
    
    status = Column(String, default="Pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="cases")
