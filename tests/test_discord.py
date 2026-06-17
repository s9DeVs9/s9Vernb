
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.discord import generate_nitro_code, generate_promo_code


class TestDiscord(unittest.TestCase):

    def test_nitro_code_length(self):
        code = generate_nitro_code()
        self.assertEqual(len(code), 16)

    def test_nitro_code_chars(self):
        code = generate_nitro_code()
        for c in code:
            self.assertIn(c, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")

    def test_promo_code_length(self):
        code = generate_promo_code("discordro")
        self.assertEqual(len(code), 16)

    def test_promo_code_different(self):
        code1 = generate_promo_code("discordro")
        code2 = generate_promo_code("discordro")
        self.assertNotEqual(code1, code2)


if __name__ == "__main__":
    unittest.main()
