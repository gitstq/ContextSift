"""核心引擎与 profile 测试。"""

import unittest

from contextsift.core import SiftEngine
from contextsift.profiles import get_profile, list_profiles
from contextsift.strategies import DropEmpty

SAMPLE = """\x1b[32mINFO build ok\x1b[0m

DEBUG something noisy
alice@example.com
same line
same line
same line
padding padding padding
"""


class TestEngine(unittest.TestCase):
    def test_basic_sift(self):
        engine = SiftEngine(profile=None)
        result = engine.sift("a\nb\na\n")
        self.assertEqual(result.text, "a\nb\na\n")
        self.assertEqual(result.stats.lines_before, 3)
        self.assertEqual(result.stats.lines_after, 3)

    def test_generic_profile(self):
        engine = SiftEngine(profile="generic")
        result = engine.sift(SAMPLE)
        self.assertNotIn("\x1b[", result.text)
        self.assertIn("[REDACTED_EMAIL]", result.text)
        self.assertIn("repeated 3x", result.text)
        self.assertGreater(result.stats.tokens.saved, 0)

    def test_custom_strategy(self):
        engine = SiftEngine(profile=None).add(DropEmpty())
        result = engine.sift("a\n\nb\n")
        self.assertEqual(result.text, "a\nb\n")

    def test_deterministic(self):
        e1 = SiftEngine(profile="test")
        e2 = SiftEngine(profile="test")
        self.assertEqual(e1.sift(SAMPLE).text, e2.sift(SAMPLE).text)

    def test_empty_input(self):
        result = SiftEngine(profile="generic").sift("")
        self.assertEqual(result.text, "")
        self.assertEqual(result.stats.lines_before, 0)

    def test_report(self):
        result = SiftEngine(profile="generic").sift(SAMPLE)
        self.assertIn("ContextSift report", result.report("text"))
        self.assertIn("tokens_before", result.report("json"))

    def test_strategies_property(self):
        engine = SiftEngine(profile="test")
        self.assertIn("strip-ansi", engine.strategies)


class TestProfiles(unittest.TestCase):
    def test_get_profile(self):
        p = get_profile("git")
        self.assertEqual(p.name, "git")

    def test_unknown(self):
        with self.assertRaises(KeyError):
            get_profile("missing")

    def test_list(self):
        names = [p["name"] for p in list_profiles()]
        for expected in ("generic", "git", "test", "build", "aggressive"):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
