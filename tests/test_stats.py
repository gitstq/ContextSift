"""Token 估算与差额统计测试。"""

import unittest

from contextsift.stats import TokenDelta, estimate_tokens


class TestEstimateTokens(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(estimate_tokens(""), 0)

    def test_ascii(self):
        self.assertEqual(estimate_tokens("hello world"), 3)
        self.assertGreater(estimate_tokens("a" * 100), estimate_tokens("a" * 50))

    def test_cjk(self):
        self.assertGreater(estimate_tokens("你好世界"), 0)
        self.assertGreater(estimate_tokens("你好世界"), estimate_tokens("hi"))

    def test_deterministic(self):
        self.assertEqual(estimate_tokens("same text"), estimate_tokens("same text"))


class TestTokenDelta(unittest.TestCase):
    def test_saved(self):
        d = TokenDelta(100, 40)
        self.assertEqual(d.saved, 60)
        self.assertEqual(d.saved_pct, 60.0)

    def test_no_negative(self):
        d = TokenDelta(10, 20)
        self.assertEqual(d.saved, 0)

    def test_zero_before(self):
        self.assertEqual(TokenDelta(0, 0).saved_pct, 0.0)

    def test_as_dict(self):
        d = TokenDelta(100, 50).as_dict()
        self.assertEqual(d["tokens_before"], 100)
        self.assertEqual(d["tokens_after"], 50)


if __name__ == "__main__":
    unittest.main()
