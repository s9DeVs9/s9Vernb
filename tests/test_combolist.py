
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.combolist import ComboList


class TestComboList(unittest.TestCase):

    def test_load_valid(self):
        cl = ComboList()
        with open("test_combos.txt", "w") as f:
            f.write("user1:pass1\nuser2:pass2\n")
        count = cl.load("test_combos.txt")
        self.assertEqual(count, 2)
        self.assertEqual(cl.combos[0], ("user1", "pass1"))
        os.remove("test_combos.txt")

    def test_load_empty_line(self):
        cl = ComboList()
        with open("test_combos.txt", "w") as f:
            f.write("user1:pass1\n\nuser2:pass2\n")
        count = cl.load("test_combos.txt")
        self.assertEqual(count, 2)
        os.remove("test_combos.txt")

    def test_load_no_colon(self):
        cl = ComboList()
        with open("test_combos.txt", "w") as f:
            f.write("nocolon\nuser1:pass1\n")
        count = cl.load("test_combos.txt")
        self.assertEqual(count, 1)
        os.remove("test_combos.txt")

    def test_add_duplicate(self):
        cl = ComboList()
        cl.add("user", "pass")
        result = cl.add("user", "pass")
        self.assertFalse(result)
        self.assertEqual(len(cl), 1)

    def test_add_new(self):
        cl = ComboList()
        result = cl.add("user", "pass")
        self.assertTrue(result)
        self.assertEqual(len(cl), 1)

    def test_remove(self):
        cl = ComboList()
        cl.add("user1", "pass1")
        cl.add("user2", "pass2")
        removed = cl.remove("user1")
        self.assertEqual(removed, 1)
        self.assertEqual(len(cl), 1)

    def test_deduplicate(self):
        cl = ComboList()
        cl.combos = [("user", "pass"), ("user", "pass")]
        removed = cl.deduplicate()
        self.assertEqual(removed, 1)
        self.assertEqual(len(cl), 1)


if __name__ == "__main__":
    unittest.main()
