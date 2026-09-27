import unittest
from app import app


class SentimentTests(unittest.TestCase):
    def test_polarity_and_input_bounds(self):
        client = app.test_client()
        self.assertEqual(client.get("/analyze/Fantastic%20services").json["sentiment"], "positive")
        self.assertEqual(
            client.get("/analyze/Terrible%20awful%20service").json["sentiment"], "negative"
        )
        self.assertEqual(client.get("/analyze/The%20car%20is%20blue").json["sentiment"], "neutral")
        self.assertEqual(client.get("/analyze/" + ("x" * 3001)).status_code, 400)


if __name__ == "__main__":
    unittest.main()
