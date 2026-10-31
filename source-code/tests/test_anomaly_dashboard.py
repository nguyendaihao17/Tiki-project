import unittest

import pandas as pd

from webapp.anomaly_page import _category_anomaly_rates, _feature_profile, _fit_outliers, _model_features, _score_distribution


class AnomalyDashboardTests(unittest.TestCase):
    def setUp(self):
        self.products = pd.DataFrame(
            {
                "category_name": ["Điện thoại"] * 10 + ["Máy tính"] * 10,
                "Kết quả": ["Bất thường"] * 2 + ["Bình thường"] * 8
                + ["Bất thường"] + ["Bình thường"] * 9,
                "Điểm bất thường": [-0.2, -0.1] + [0.1] * 8
                + [-0.05] + [0.2] * 9,
            }
        )

    def test_category_rate_uses_actual_anomaly_counts(self):
        rates = _category_anomaly_rates(self.products).set_index("Danh mục")
        self.assertEqual(rates.loc["Điện thoại", "Sản phẩm"], 10)
        self.assertEqual(rates.loc["Điện thoại", "Bất thường"], 2)
        self.assertEqual(rates.loc["Điện thoại", "Tỷ lệ (%)"], 20)
        self.assertEqual(rates.loc["Máy tính", "Tỷ lệ (%)"], 10)

    def test_score_distribution_preserves_group_totals(self):
        distribution = _score_distribution(self.products)
        totals = distribution.groupby("Kết quả")["Sản phẩm"].sum()
        self.assertEqual(totals["Bất thường"], 3)
        self.assertEqual(totals["Bình thường"], 17)

    def test_model_uses_one_revenue_field_and_the_five_reported_inputs(self):
        products = pd.DataFrame(columns=[
            "price", "discount_rate", "quantity_sold", "revenue_estimate",
            "estimated_revenue", "review_count", "rating_average",
        ])
        self.assertEqual(_model_features(products), [
            "price", "discount_rate", "quantity_sold", "revenue_estimate", "review_count",
        ])
        self.assertEqual(
            _model_features(products.drop(columns="revenue_estimate")),
            ["price", "discount_rate", "quantity_sold", "estimated_revenue", "review_count"],
        )

    def test_extreme_product_is_flagged_without_replacing_complete_values(self):
        regular = pd.DataFrame({
            "price": [100 + n for n in range(49)],
            "discount_rate": [n % 10 for n in range(49)],
            "quantity_sold": [10 + n % 7 for n in range(49)],
            "revenue_estimate": [1000 + n * 10 for n in range(49)],
            "review_count": [n % 5 for n in range(49)],
        })
        extreme = pd.DataFrame([{
            "price": 1_000_000, "discount_rate": 90, "quantity_sold": 100_000,
            "revenue_estimate": 100_000_000_000, "review_count": 10_000,
        }])
        labels, scores = _fit_outliers(pd.concat([regular, extreme], ignore_index=True), .02)
        self.assertEqual(labels[-1], -1)
        self.assertLess(scores[-1], scores[:-1].min())

    def test_feature_profile_places_anomalies_in_dataset_deciles(self):
        features = pd.DataFrame({
            "price": range(1, 11),
            "discount_rate": range(1, 11),
            "quantity_sold": range(1, 11),
            "revenue_estimate": range(1, 11),
            "review_count": range(1, 11),
        })
        profile = _feature_profile(features, [True] + [False] * 8 + [True])
        totals = profile.groupby("Chỉ số")["Sản phẩm"].sum()
        self.assertEqual(len(totals), 5)
        self.assertTrue(totals.eq(2).all())
        prices = profile.set_index(["Chỉ số", "Phân vị"])
        self.assertEqual(prices.loc[("Giá", "0–10%"), "Sản phẩm"], 1)
        self.assertEqual(prices.loc[("Giá", "90–100%"), "Sản phẩm"], 1)


if __name__ == "__main__":
    unittest.main()
