
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.platforms import PLATFORMS


class TestPlatforms(unittest.TestCase):

    def test_platforms_not_empty(self):
        self.assertGreater(len(PLATFORMS), 0)

    def test_platform_has_required_keys(self):
        for name, p in PLATFORMS.items():
            self.assertTrue(hasattr(p, "name"))
            self.assertTrue(hasattr(p, "login_url"))
            self.assertTrue(hasattr(p, "method"))


if __name__ == "__main__":
    unittest.main()
