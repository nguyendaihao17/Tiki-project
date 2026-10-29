import unittest

import pandas as pd

from webapp.clustering_page import _cluster_size_table, _customer_features, _seller_features


class SellerClusteringFeatureTests(unittest.TestCase):
    def test_aggregates_product_portfolio_by_seller(self):
        products = pd.DataFrame(
            [
                {"seller_id": "seller-a", "product_id": "p1", "quantity_sold": 4,
                 "estimated_revenue": 100, "rating_average": 4.0, "review_count": 10},
                {"seller_id": "seller-a", "product_id": "p2", "quantity_sold": 6,
                 "estimated_revenue": 200, "rating_average": 2.0, "review_count": 2},
                {"seller_id": "seller-b", "product_id": "p3", "quantity_sold": 3,
                 "estimated_revenue": 90, "rating_average": 5.0, "review_count": 5},
            ]
        )

        features = _seller_features(products).set_index("seller_id")

        self.assertEqual(features.loc["seller-a", "product_count"], 2)
        self.assertEqual(features.loc["seller-a", "quantity_sold"], 10)
        self.assertEqual(features.loc["seller-a", "estimated_revenue"], 300)
        self.assertEqual(features.loc["seller-a", "review_count"], 12)
        self.assertEqual(features.loc["seller-a", "average_rating"], 3.0)

    def test_requires_seller_identifier(self):
        self.assertTrue(_seller_features(pd.DataFrame({"product_id": ["p1"]})).empty)

    def test_aggregates_review_behavior_by_customer(self):
        reviews = pd.DataFrame(
            [
                {"customer_id": "customer-a", "product_id": "p1", "rating": 5},
                {"customer_id": "customer-a", "product_id": "p2", "rating": 1},
                {"customer_id": "customer-b", "product_id": "p3", "rating": 4},
            ]
        )

        features = _customer_features(reviews).set_index("customer_id")

        self.assertEqual(features.loc["customer-a", "review_count"], 2)
        self.assertEqual(features.loc["customer-a", "unique_products"], 2)
        self.assertEqual(features.loc["customer-a", "average_rating"], 3.0)
        self.assertEqual(features.loc["customer-a", "negative_review_rate"], 0.5)

    def test_builds_cluster_size_table_for_visualization(self):
        records = pd.DataFrame(
            {"cluster": [2, 0, 2, 1], "seller_id": ["a", "b", "c", "d"]}
        )

        sizes = _cluster_size_table(records, "seller_id", "Nhà bán")

        self.assertEqual(sizes["Cụm"].tolist(), [0, 1, 2])
        self.assertEqual(sizes["Nhà bán"].tolist(), [1, 1, 2])


if __name__ == "__main__":
    unittest.main()
