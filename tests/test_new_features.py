
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from features.credential.password_generator import PasswordGenerator
from features.credential.wordlist_generator import WordlistGenerator
from features.security.token_generator import TokenGenerator


class TestPasswordGenerator(unittest.TestCase):

    def test_generate_one(self):
        gen = PasswordGenerator(length=16)
        pw = gen.generate_one()
        self.assertEqual(len(pw), 16)

    def test_generate_batch(self):
        gen = PasswordGenerator(length=12)
        passwords = gen.generate_batch(10)
        self.assertEqual(len(passwords), 10)
        for pw in passwords:
            self.assertEqual(len(pw), 12)

    def test_strength(self):
        gen = PasswordGenerator()
        result = gen.estimate_strength("abc")
        self.assertEqual(result["strength"], "WEAK")
        result = gen.estimate_strength("aB3!eF5@kJ9#mN1$")
        self.assertIn(result["strength"], ("STRONG", "VERY STRONG"))


class TestWordlistGenerator(unittest.TestCase):

    def test_from_name(self):
        gen = WordlistGenerator()
        words = gen.generate_from_name("test")
        self.assertGreater(len(words), 0)
        self.assertIn("test", words)
        self.assertIn("Test", words)

    def test_from_domain(self):
        gen = WordlistGenerator()
        words = gen.generate_from_domain("example.com")
        self.assertGreater(len(words), 0)

    def test_leet(self):
        gen = WordlistGenerator()
        gen.generate_from_name("test")
        gen.apply_leet()
        words = gen.get_wordlist()
        self.assertGreater(len(words), 10)


class TestTokenGenerator(unittest.TestCase):

    def test_generate_jwt(self):
        gen = TokenGenerator()
        token = gen.generate_jwt({"sub": "user123"}, "secret123")
        self.assertEqual(len(token.split(".")), 3)

    def test_decode_jwt(self):
        gen = TokenGenerator()
        token = gen.generate_jwt({"sub": "user123"}, "secret123")
        result = gen.decode_jwt(token)
        self.assertTrue(result.get("valid_format"))
        self.assertEqual(result["payload"]["sub"], "user123")

    def test_validate_jwt(self):
        gen = TokenGenerator()
        token = gen.generate_jwt({"sub": "user123"}, "secret123")
        result = gen.validate_jwt(token, "secret123")
        self.assertTrue(result["valid"])
        self.assertTrue(result["signature_valid"])

    def test_validate_wrong_secret(self):
        gen = TokenGenerator()
        token = gen.generate_jwt({"sub": "user123"}, "secret123")
        result = gen.validate_jwt(token, "wrong_secret")
        self.assertFalse(result["valid"])
        self.assertFalse(result["signature_valid"])

    def test_generate_api_key(self):
        gen = TokenGenerator()
        key = gen.generate_api_key()
        self.assertEqual(len(key), 43)


if __name__ == "__main__":
    unittest.main()
