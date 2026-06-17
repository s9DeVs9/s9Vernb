
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.classifier import classify_response
from core.platforms import Platform
from core.utils import ResultStatus


class TestClassifier(unittest.TestCase):

    def setUp(self):
        self.platform = Platform(
            name="test",
            login_url="http://test.com",
            success_indicators=["welcome", "dashboard"],
            fail_indicators=["invalid", "wrong"],
        )

    def test_valid_response(self):
        status, reason = classify_response(200, "welcome", {}, "", self.platform)
        self.assertEqual(status, ResultStatus.VALID)

    def test_invalid_response(self):
        status, reason = classify_response(200, "invalid password", {}, "", self.platform)
        self.assertEqual(status, ResultStatus.INVALID)

    def test_error_500(self):
        status, reason = classify_response(500, "", {}, "", self.platform)
        self.assertEqual(status, ResultStatus.ERROR)

    def test_ratelimit(self):
        status, reason = classify_response(429, "", {}, "", self.platform)
        self.assertEqual(status, ResultStatus.INVALID)


if __name__ == "__main__":
    unittest.main()
