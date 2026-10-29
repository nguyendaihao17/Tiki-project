import unittest

import pandas as pd

from webapp.anomaly_page import _category_anomaly_rates, _score_distribution


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


if __name__ == "__main__":
    unittest.main()
