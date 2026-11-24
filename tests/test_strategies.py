"""压缩策略单元测试。"""

import unittest

from contextsift.strategies import (
    CollapseRepeats,
    DedupeLines,
    DropEmpty,
    HeadTail,
    MaxLines,
    NumberLines,
    RedactSecrets,
    SiftContext,
    SqueezeBlank,
    StripAnsi,
    StripNoise,
    TokenBudget,
    TruncateLines,
    get_strategy,
    list_strategies,
)

CTX = SiftContext()


class TestStrategies(unittest.TestCase):
    def test_strip_ansi(self):
        self.assertEqual(StripAnsi().apply(["\x1b[31mred\x1b[0m"], CTX), ["red"])

    def test_squeeze_blank(self):
        self.assertEqual(SqueezeBlank().apply(["a", "", "", "", "b"], CTX), ["a", "", "b"])

    def test_collapse_repeats(self):
        lines = ["x", "x", "x", "x", "y"]
        out = CollapseRepeats(min_run=3).apply(lines, CTX)
        self.assertIn("repeated 4x", out[-1] if False else "\n".join(out))

    def test_dedupe(self):
        self.assertEqual(DedupeLines().apply(["a", "b", "a", "c"], CTX), ["a", "b", "c"])

    def test_strip_noise(self):
        out = StripNoise().apply(["DEBUG x", "INFO y", "TRACE z"], CTX)
        self.assertEqual(out, ["INFO y"])

    def test_truncate(self):
        out = TruncateLines(max_chars=5).apply(["abcdefgh"], CTX)
        self.assertTrue(out[0].startswith("abcde"))
        self.assertIn("+3 chars", out[0])

    def test_head_tail(self):
        lines = [str(i) for i in range(100)]
        out = HeadTail(head=3, tail=3).apply(lines, CTX)
        self.assertEqual(len(out), 7)
        self.assertIn("94 lines omitted", out[3])

    def test_max_lines(self):
        lines = [str(i) for i in range(100)]
        out = MaxLines(max_lines=10).apply(lines, CTX)
        self.assertEqual(len(out), 11)
        self.assertIn("sampled 10/100", out[0])

    def test_redact_secrets(self):
        out = RedactSecrets().apply(["key abc@example.com"], CTX)
        self.assertIn("[REDACTED_EMAIL]", out[0])

    def test_number_lines(self):
        self.assertEqual(NumberLines().apply(["a", "b"], CTX), ["   1| a", "   2| b"])

    def test_token_budget(self):
        lines = ["word " * 20 for _ in range(50)]
        out = TokenBudget(budget=30).apply(lines, CTX)
        self.assertLess(len(out), 50)

    def test_drop_empty(self):
        self.assertEqual(DropEmpty().apply(["a", "", "b"], CTX), ["a", "b"])

    def test_get_strategy_unknown(self):
        with self.assertRaises(KeyError):
            get_strategy("nope")

    def test_list_strategies(self):
        names = [s["name"] for s in list_strategies()]
        self.assertIn("dedupe", names)
        self.assertGreaterEqual(len(names), 10)


if __name__ == "__main__":
    unittest.main()
