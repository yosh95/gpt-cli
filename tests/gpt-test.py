import unittest
from gpt import expand_page_range

class TestExpandPageRange(unittest.TestCase):
    def test_expand_single_number(self):
        self.assertEqual(expand_page_range("1"), [1])

    def test_expand_multiple_numbers(self):
        self.assertEqual(expand_page_range("1,2"), [1, 2])

    def test_expand_range(self):
        self.assertEqual(expand_page_range("1-3"), [1, 2, 3])

    def test_expand_complex_range(self):
        self.assertEqual(expand_page_range("1,3-5"), [1, 3, 4, 5])

    def test_expand_with_invalid_characters(self):
        with self.assertRaises(ValueError):
            expand_page_range("1,a")

    def test_expand_with_negative_range(self):
        with self.assertRaises(ValueError):
            # Assuming your function does not support negative ranges, 
            # this test should pass by throwing a ValueError.
            # If your function supports negatives, adjust this test accordingly.
            expand_page_range("-3--1")

# This allows the test script to be run directly from the command line.
if __name__ == '__main__':
    unittest.main()

