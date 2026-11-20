import unittest

from api_security import is_allowed_request_origin


class RequestOriginTests(unittest.TestCase):
    def test_allows_requests_without_a_browser_origin(self):
        self.assertTrue(is_allowed_request_origin(None))

    def test_allows_chrome_extension_origins(self):
        self.assertTrue(is_allowed_request_origin("chrome-extension://" + "a" * 32))

    def test_rejects_web_origins_and_malformed_extension_origins(self):
        for origin in (
            "https://attacker.example",
            "http://localhost:5000",
            "null",
            "chrome-extension://short-id",
            "chrome-extension://" + "a" * 32 + ".attacker.example",
            "chrome-extension://" + "a" * 31 + "q",
        ):
            with self.subTest(origin=origin):
                self.assertFalse(is_allowed_request_origin(origin))


if __name__ == "__main__":
    unittest.main()
