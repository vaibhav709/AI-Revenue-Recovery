import joblib
import pandas as pd

from ml.prediction_schema import PaymentRisk


MODEL_PATH = "ml/xgb_payment_failure_model.pkl"
FEATURES_PATH = "ml/feature_columns.pkl"

FAILURE_THRESHOLD = 0.50


# Load model and feature list
model = joblib.load(MODEL_PATH)
feature_columns = joblib.load(FEATURES_PATH)


def predict_payment_failure(customer_data, customer_id):
    """
    Predict payment failure probability and risk level.
    """

    # Convert customer data into DataFrame
    customer_df = pd.DataFrame([customer_data])

    # Make sure features are in the exact order used during training
    customer_df = customer_df[feature_columns]

    # Predict probability of payment failure
    failure_probability = model.predict_proba(customer_df)[0][1]

    # Apply selected ML threshold
    predicted_failure = failure_probability >= FAILURE_THRESHOLD

    # Business risk classification
    if failure_probability < 0.30:
        risk_level = "LOW"
    elif failure_probability < 0.60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return PaymentRisk(
        customer_id=customer_id,
        failure_probability=round(float(failure_probability), 4),
        predicted_failure=bool(predicted_failure),
        risk_level=risk_level,

        num_delayed_payments=int(
            customer_data["num_delayed_payments"]
        ),

        max_payment_delay=int(
            customer_data["max_payment_delay"]
        ),

        avg_payment_delay=float(
            customer_data["avg_payment_delay"]
        ),

        recent_payment_delay=int(
            customer_data["recent_payment_delay"]
        ),

        credit_utilization=float(
            customer_data["credit_utilization"]
        ),

        payment_to_bill_ratio=float(
            customer_data["payment_to_bill_ratio"]
        ),

        recent_payment_ratio=float(
            customer_data["recent_payment_ratio"]
        ),

        recent_payment_amount=float(
            customer_data["recent_payment_amount"]
        ),

        recent_bill_amount=float(
            customer_data["recent_bill_amount"]
        )
    )