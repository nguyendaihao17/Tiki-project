import unittest

import pandas as pd

from webapp.forecast_page import _build_model, _evaluation_frame, _load_reference_products


class ForecastVisualizationTests(unittest.TestCase):
    def test_builds_actual_prediction_and_residual_values_for_charts(self):
        evaluation = _evaluation_frame([10, 20, 30], [12, 17, 30])

        self.assertEqual(evaluation.columns.tolist(), ["Thực tế", "Ước lượng", "Sai số"])
        self.assertEqual(evaluation["Thực tế"].tolist(), [10.0, 20.0, 30.0])
        self.assertEqual(evaluation["Ước lượng"].tolist(), [12.0, 17.0, 30.0])
        self.assertEqual(evaluation["Sai số"].tolist(), [2.0, -3.0, 0.0])

    def test_evaluation_keeps_every_holdout_row_with_nonconsecutive_indexes(self):
        actual = pd.Series([10, 20, 30], index=[11, 4, 27])

        evaluation = _evaluation_frame(actual, [12, 17, 30])

        self.assertEqual(len(evaluation), 3)
        self.assertEqual(evaluation["Thực tế"].tolist(), [10, 20, 30])
        self.assertEqual(evaluation["Ước lượng"].tolist(), [12, 17, 30])

    def test_same_snapshot_reuses_fitted_model(self):
        products = _load_reference_products().iloc[:60].copy()
        first, _, _, error = _build_model(products)
        second, _, _, _ = _build_model(products.copy())
        self.assertIsNone(error)
        self.assertIs(first, second)

    def test_report_snapshot_reproduces_published_metrics(self):
        products = _load_reference_products()
        model, metrics, details, error = _build_model(products)

        self.assertIsNone(error)
        numeric, categorical, X, _, evaluation = details
        self.assertEqual(len(products), 2307)
        self.assertEqual(len(X), 2307)
        self.assertEqual(len(evaluation), 462)
        self.assertEqual(numeric, [
            "price", "original_price", "discount", "discount_rate",
            "rating_average", "review_count",
        ])
        self.assertEqual(categorical, [
            "price_segment", "seller_type", "is_official_store",
            "is_authentic", "is_freeship_xtra",
        ])
        self.assertEqual(model.named_steps["regressor"].n_estimators, 100)
        self.assertFalse(model.named_steps["preprocessor"].transformers_[1][1].sparse_output)
        self.assertAlmostEqual(metrics["MAE"], 3248.354136, places=5)
        self.assertAlmostEqual(metrics["RMSE"], 14561.485227, places=5)
        self.assertAlmostEqual(metrics["R2"], 0.271445478, places=8)

    def test_drops_rows_missing_report_features(self):
        products = _load_reference_products().iloc[:60].copy()
        products.loc[products.index[0], "discount"] = None
        products.loc[products.index[1], "seller_type"] = None

        _, _, details, error = _build_model(products)

        self.assertIsNone(error)
        self.assertEqual(len(details[2]), 58)

    def test_requires_all_report_features(self):
        products = _load_reference_products().drop(columns="is_authentic")

        _, _, _, error = _build_model(products)

        self.assertIn("is_authentic", error)


if __name__ == "__main__":
    unittest.main()
