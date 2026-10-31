import unittest
from unittest.mock import Mock, patch

from src.analytics import DASHBOARD_REVIEW_PROJECTION, load_dashboard_reviews_data


class DashboardReviewLoadingTests(unittest.TestCase):
    def setUp(self):
        load_dashboard_reviews_data.clear()

    def tearDown(self):
        load_dashboard_reviews_data.clear()

    def test_dashboard_loader_requests_only_required_review_fields(self):
        collection = Mock()
        collection.find.return_value = [{"review_id": 1, "product_id": 7, "rating": 5}]
        with patch("src.analytics.get_clean_collection", return_value=collection):
            reviews = load_dashboard_reviews_data()

        collection.find.assert_called_once_with({}, DASHBOARD_REVIEW_PROJECTION)
        self.assertEqual(reviews.columns.tolist(), ["review_id", "product_id", "rating"])


if __name__ == "__main__":
    unittest.main()
