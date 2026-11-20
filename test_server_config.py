import unittest

from server_config import debug_mode_enabled


class DebugModeTests(unittest.TestCase):
    def test_debug_is_off_by_default_or_for_false_values(self):
        for value in (None, "", "0", "false", "no", "off", "2"):
            with self.subTest(value=value):
                self.assertFalse(debug_mode_enabled(value))

    def test_debug_requires_an_explicit_truthy_value(self):
        for value in ("1", "true", "TRUE", " yes "):
            with self.subTest(value=value):
                self.assertTrue(debug_mode_enabled(value))


if __name__ == "__main__":
    unittest.main()
