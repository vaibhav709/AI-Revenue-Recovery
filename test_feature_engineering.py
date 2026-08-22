import unittest
from api.main import compute_derived_features

class FeatureEngineeringTests(unittest.TestCase):
    def test_avg_payment_delay(self):
        # Should sum positive delays and divide by 6
        data = {
            'pay_status_1': 1, 'pay_status_2': 2, 'pay_status_3': -1,
            'pay_status_4': 0, 'pay_status_5': 0, 'pay_status_6': 0,
            'bill_amount_1': 100, 'bill_amount_2': 100, 'bill_amount_3': 100,
            'bill_amount_4': 100, 'bill_amount_5': 100, 'bill_amount_6': 100,
            'payment_amount_1': 100, 'payment_amount_2': 100, 'payment_amount_3': 100,
            'payment_amount_4': 100, 'payment_amount_5': 100, 'payment_amount_6': 100,
            'credit_limit': 1000,
        }
        computed = compute_derived_features(data)
        self.assertEqual(computed['avg_payment_delay'], 3.0 / 6.0)

    def test_payment_to_bill_ratio_clipping_and_zero(self):
        data = {
            'pay_status_1': 0, 'pay_status_2': 0, 'pay_status_3': 0,
            'pay_status_4': 0, 'pay_status_5': 0, 'pay_status_6': 0,
            'bill_amount_1': 0, 'bill_amount_2': 0, 'bill_amount_3': 0,
            'bill_amount_4': 0, 'bill_amount_5': 0, 'bill_amount_6': 0,
            'payment_amount_1': 100, 'payment_amount_2': 100, 'payment_amount_3': 100,
            'payment_amount_4': 100, 'payment_amount_5': 100, 'payment_amount_6': 100,
            'credit_limit': 1000,
        }
        # zero denominator
        computed = compute_derived_features(data)
        self.assertEqual(computed['payment_to_bill_ratio'], 0.0)

        # > 5
        data['bill_amount_1'] = 1
        computed = compute_derived_features(data)
        self.assertEqual(computed['payment_to_bill_ratio'], 5.0)

    def test_credit_utilization_clipping(self):
        data = {
            'pay_status_1': 0, 'pay_status_2': 0, 'pay_status_3': 0,
            'pay_status_4': 0, 'pay_status_5': 0, 'pay_status_6': 0,
            'bill_amount_1': 10000, 'bill_amount_2': 10000, 'bill_amount_3': 10000,
            'bill_amount_4': 10000, 'bill_amount_5': 10000, 'bill_amount_6': 10000,
            'payment_amount_1': 100, 'payment_amount_2': 100, 'payment_amount_3': 100,
            'payment_amount_4': 100, 'payment_amount_5': 100, 'payment_amount_6': 100,
            'credit_limit': 1000,
        }
        computed = compute_derived_features(data)
        # avg_bill = 10000, credit_limit = 1000 -> ratio 10. clipped to 5.
        self.assertEqual(computed['credit_utilization'], 5.0)
        
    def test_recent_payment_ratio_clipping_and_zero(self):
        data = {
            'pay_status_1': 0, 'pay_status_2': 0, 'pay_status_3': 0,
            'pay_status_4': 0, 'pay_status_5': 0, 'pay_status_6': 0,
            'bill_amount_1': 0, 'bill_amount_2': 0, 'bill_amount_3': 0,
            'bill_amount_4': 0, 'bill_amount_5': 0, 'bill_amount_6': 0,
            'payment_amount_1': 1000, 'payment_amount_2': 100, 'payment_amount_3': 100,
            'payment_amount_4': 100, 'payment_amount_5': 100, 'payment_amount_6': 100,
            'credit_limit': 1000,
        }
        # zero denominator
        computed = compute_derived_features(data)
        self.assertEqual(computed['recent_payment_ratio'], 0.0)

        # > 5
        data['bill_amount_1'] = 10
        computed = compute_derived_features(data)
        self.assertEqual(computed['recent_payment_ratio'], 5.0)

if __name__ == '__main__':
    unittest.main()
