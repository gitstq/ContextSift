"""脱敏规则测试。"""

import unittest

from contextsift.redact import redact


class TestRedact(unittest.TestCase):
    def test_ghp_token(self):
        text = "token=ghp_" + "a" * 30
        out, hits = redact(text)
        self.assertIn("[REDACTED_GHP_TOKEN]", out)
        self.assertNotIn("a" * 30, out)
        self.assertGreater(hits, 0)

    def test_email(self):
        out, _ = redact("contact alice@example.com now")
        self.assertIn("[REDACTED_EMAIL]", out)
        self.assertNotIn("alice@example.com", out)

    def test_api_key_kv(self):
        out, _ = redact('api_key = "supersecretvalue123"')
        self.assertIn("[REDACTED]", out)
        self.assertNotIn("supersecretvalue123", out)

    def test_no_hit(self):
        out, hits = redact("just plain text")
        self.assertEqual(out, "just plain text")
        self.assertEqual(hits, 0)


if __name__ == "__main__":
    unittest.main()
