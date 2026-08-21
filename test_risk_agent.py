from crew.pipeline import run_recovery_pipeline


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


def main() -> None:
    """Run the Phase 7 end-to-end regression/integration test."""
    final_plan = run_recovery_pipeline(customer_data, customer_id=8681)
    print("\n===== COMPLETE FINAL RECOVERY PLAN =====")
    print(final_plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
