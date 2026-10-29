import unittest

from webapp.forecast_page import _evaluation_frame


class ForecastVisualizationTests(unittest.TestCase):
    def test_builds_actual_prediction_and_residual_values_for_charts(self):
        evaluation = _evaluation_frame([10, 20, 30], [12, 17, 30])

        self.assertEqual(evaluation.columns.tolist(), ["Thực tế", "Ước lượng", "Sai số"])
        self.assertEqual(evaluation["Thực tế"].tolist(), [10.0, 20.0, 30.0])
        self.assertEqual(evaluation["Ước lượng"].tolist(), [12.0, 17.0, 30.0])
        self.assertEqual(evaluation["Sai số"].tolist(), [2.0, -3.0, 0.0])


if __name__ == "__main__":
    unittest.main()
