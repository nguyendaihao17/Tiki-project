import unittest

import pandas as pd

from webapp.dashboard_page import (
    _category_table, _discount_band_table, _price_category_table, _price_segment_table,
    _portfolio_concentration_table, _review_coverage_category_table, _review_coverage_table,
    _review_category_table, _review_trend_table, _seller_comparison, _seller_table,
    _service_mix_table, _top_product_category_table,
    dashboard_summary, filter_dashboard_data,
)
from webapp.explore_page import _filter_products as filter_explore_products


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.products = pd.DataFrame([
            {"product_id": 1, "category_name": "A", "price": 100, "quantity_sold": 2,
             "estimated_revenue": 200, "rating_average": 2, "is_tiki_now": True, "seller_id": "s1"},
            {"product_id": 2, "category_name": "B", "price": 200, "quantity_sold": 1,
             "estimated_revenue": 200, "rating_average": 5, "is_tiki_now": False, "seller_id": "s2"},
        ])
        self.reviews = pd.DataFrame([
            {"product_id": "1", "rating": 1, "created_at": "2026-01-01"},
            {"product_id": "1", "rating": 5, "created_at": "2026-02-01"},
            {"product_id": "2", "rating": 4, "created_at": "2026-01-01"},
        ])

    def test_product_filters_scope_reviews_and_keep_revenue_consistent(self):
        products, reviews = filter_dashboard_data(self.products, self.reviews,
                                                  categories=["A"], tiki_now="Có")
        summary = dashboard_summary(products, reviews)
        self.assertEqual((summary["products"], summary["reviews"], summary["revenue"]), (1, 2, 200))
        self.assertEqual(summary["risk"], 1)

    def test_review_dates_do_not_change_product_revenue(self):
        products, reviews = filter_dashboard_data(self.products, self.reviews,
                                                  review_dates=(pd.Timestamp("2026-02-01").date(),
                                                                pd.Timestamp("2026-02-01").date()))
        summary = dashboard_summary(products, reviews)
        self.assertEqual(summary["revenue"], 400)
        self.assertEqual(summary["reviews"], 1)
        self.assertEqual(summary["rating"], 5)

    def test_main_category_filter_matches_product_root_category(self):
        products = self.products.assign(root_category_name=["Điện tử", "Gia dụng"])
        filtered, reviews = filter_dashboard_data(products, self.reviews, categories=["Điện tử"])
        self.assertEqual(filtered["product_id"].tolist(), [1])
        self.assertEqual(len(reviews), 2)

    def test_explore_uses_the_same_main_category(self):
        products = self.products.assign(root_category_name=["Điện tử", "Gia dụng"])
        filtered = filter_explore_products(products, "", ["Gia dụng"], [], None, None, None)
        self.assertEqual(filtered["product_id"].tolist(), [2])

    def test_category_share_and_price_segment_use_filtered_products(self):
        products = self.products.assign(price_segment=["Giá rẻ", "Cao cấp"])
        category = _category_table(products)
        segments = _price_segment_table(products)
        self.assertAlmostEqual(category["Tỷ trọng (%)"].sum(), 100)
        self.assertAlmostEqual(category["Lũy kế (%)"].iloc[-1], 100)
        self.assertEqual(segments["Đã bán"].sum(), 3)
        self.assertEqual(segments["Doanh thu ước tính"].sum(), 400)

    def test_negative_review_rate_and_seller_share(self):
        category = _review_category_table(self.products, self.reviews).set_index("Danh mục")
        self.assertEqual(category.loc["A", "Lượt đánh giá"], 2)
        self.assertEqual(category.loc["A", "Tỷ lệ 1–2 sao (%)"], 50)
        self.assertEqual(category.loc["B", "Tỷ lệ 1–2 sao (%)"], 0)
        self.assertAlmostEqual(_seller_table(self.products)["Tỷ trọng (%)"].sum(), 100)
        summary = dashboard_summary(self.products, self.reviews)
        self.assertAlmostEqual(summary["negative_rate"], 100 / 3)
        self.assertEqual(summary["risk_rate"], 50)

    def test_review_trend_keeps_rating_mix_and_uses_years_for_long_ranges(self):
        reviews = pd.DataFrame({
            "created_at": pd.date_range("2022-01-01", periods=37, freq="MS"),
            "rating": [5] * 36 + [1],
        })
        trend, annual = _review_trend_table(reviews)
        self.assertTrue(annual)
        self.assertEqual(trend["Lượt đánh giá"].sum(), 37)
        self.assertEqual(set(trend["Sao"]), {1, 5})

    def test_seller_comparison_keeps_dominant_seller_explicit(self):
        sellers = pd.DataFrame({"Nhà bán": ["A", "B", "C"], "Tỷ trọng (%)": [90, 6, 4]})
        comparison, leader = _seller_comparison(sellers)
        self.assertEqual(leader["Nhà bán"], "A")
        self.assertEqual(comparison["Nhà bán"].tolist(), ["B", "C"])
        comparison, leader = _seller_comparison(sellers.assign(**{"Tỷ trọng (%)": [50, 30, 20]}))
        self.assertIsNone(leader)
        self.assertEqual(len(comparison), 3)

    def test_price_dashboard_uses_valid_discounts_and_category_quartiles(self):
        products = self.products.assign(discount_rate=[0, 20])
        bands = _discount_band_table(products).set_index("Mức giảm")
        self.assertEqual(bands["Sản phẩm"].sum(), 2)
        self.assertEqual(bands.loc["Không giảm", "Đã bán/SP"], 2)
        self.assertEqual(bands.loc["11–25%", "Đã bán/SP"], 1)
        quartiles = _price_category_table(products).set_index("Danh mục")
        self.assertEqual(quartiles.loc["A", "Trung vị"], 100)
        self.assertEqual(quartiles.loc["B", "Q3"], 200)

    def test_service_dashboard_shares_follow_filtered_products(self):
        products = self.products.assign(is_freeship_xtra=[True, False])
        table = _service_mix_table(products)
        self.assertEqual(len(table), 4)
        self.assertEqual(table["Sản phẩm"].sum(), 2)
        self.assertAlmostEqual(table["Tỷ trọng sản phẩm (%)"].sum(), 100)
        self.assertAlmostEqual(table["Tỷ trọng doanh thu (%)"].sum(), 100)
        filtered, _ = filter_dashboard_data(products, self.reviews, categories=["A"])
        focused = _service_mix_table(filtered)
        both = focused[focused["TikiNOW"].eq("Có") & focused["Freeship Xtra"].eq("Có")].iloc[0]
        self.assertEqual((both["Sản phẩm"], both["Tỷ trọng sản phẩm (%)"]), (1, 100))

    def test_portfolio_concentration_uses_filtered_nonnegative_revenue(self):
        products = pd.DataFrame({"estimated_revenue": [90, 10, -5] + [0] * 7})
        curve = _portfolio_concentration_table(products).set_index("Tỷ lệ sản phẩm đứng đầu (%)")
        self.assertEqual(curve.loc[0, "Tỷ lệ doanh thu lũy kế (%)"], 0)
        self.assertEqual(curve.loc[10, "Tỷ lệ doanh thu lũy kế (%)"], 90)
        self.assertEqual(curve.loc[100, "Tỷ lệ doanh thu lũy kế (%)"], 100)
        self.assertTrue(_portfolio_concentration_table(products.iloc[2:]).empty)
        top = _top_product_category_table(products.assign(category_name=["A"] * 10))
        self.assertEqual((top.iloc[0]["Sản phẩm"], top.iloc[0]["Doanh thu ước tính"]), (1, 90))

    def test_review_coverage_uses_valid_product_review_counts(self):
        products = pd.DataFrame({
            "review_count": [0, 5, 100, None, -1],
            "estimated_revenue": [100, 200, 700, 400, 500],
        })
        table = _review_coverage_table(products).set_index("Lượt đánh giá/SP")
        self.assertEqual(table["Sản phẩm"].sum(), 3)
        self.assertAlmostEqual(table.loc["0", "Tỷ trọng sản phẩm (%)"], 100 / 3)
        self.assertEqual(table.loc["≥100", "Tỷ trọng doanh thu (%)"], 70)
        categories = _review_coverage_category_table(products.assign(category_name=["A", "A", "B", "B", "B"]))
        self.assertEqual(categories.set_index("Danh mục").loc["A", "Tỷ lệ có đánh giá (%)"], 50)


if __name__ == "__main__":
    unittest.main()
