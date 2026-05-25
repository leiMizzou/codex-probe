"""Tests for the response validators and small text helpers."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import provider_probe as pp


class TestNormalization(unittest.TestCase):
    def test_norm_collapses_whitespace(self):
        self.assertEqual(pp.norm("  a   b\tc\n"), "a b c")

    def test_norm_loose_strips_non_alnum_and_lowercases(self):
        self.assertEqual(pp.norm_loose(" Foo-Bar.BAZ_42 "), "foo-bar.baz_42")
        self.assertEqual(pp.norm_loose("HELLO, World!"), "helloworld")


class TestValidators(unittest.TestCase):
    def test_exact_matches_ignoring_case_and_punct(self):
        v = pp.exact("Paris")
        self.assertTrue(v(" paris "))
        self.assertTrue(v("PARIS!"))
        self.assertFalse(v("London"))

    def test_exact_multiline_compares_lines(self):
        v = pp.exact_multiline("alpha\nbeta\ngamma")
        self.assertTrue(v("alpha\nbeta\ngamma"))
        self.assertTrue(v("  alpha\nbeta\ngamma\n"))
        self.assertFalse(v("alpha\nbeta"))
        self.assertFalse(v("alpha\nBETA\ngamma"))

    def test_contains_all_case_insensitive(self):
        v = pp.contains_all("foo", "bar")
        self.assertTrue(v("FOO and bar"))
        self.assertFalse(v("only foo"))

    def test_json_equals(self):
        v = pp.json_equals({"x": 1, "y": [2, 3]})
        self.assertTrue(v('{"x": 1, "y": [2, 3]}'))
        self.assertTrue(v('{"y": [2, 3], "x": 1}'))
        self.assertFalse(v('{"x": 1}'))
        self.assertFalse(v("not json"))

    def test_json_has_paris_requires_shape(self):
        self.assertTrue(pp.json_has_paris('{"answer": "Paris", "reason": "capital of France"}'))
        # Empty reason → fail
        self.assertFalse(pp.json_has_paris('{"answer": "Paris", "reason": ""}'))
        # Extra key → fail
        self.assertFalse(pp.json_has_paris('{"answer": "Paris", "reason": "x", "extra": 1}'))
        # Wrong answer → fail
        self.assertFalse(pp.json_has_paris('{"answer": "London", "reason": "x"}'))
        # Not JSON → fail
        self.assertFalse(pp.json_has_paris("Paris because..."))

    def test_every_suite_case_validator_accepts_expected(self):
        # The packaged HARD_SUITE is the runtime contract; every case's validator
        # must accept its own canonical expected answer.
        for case in pp.HARD_SUITE:
            with self.subTest(case=case.case_id):
                self.assertTrue(
                    case.validator(case.expected),
                    f"validator for {case.case_id} rejected its own expected answer",
                )

    def test_every_suite_case_validator_rejects_obvious_garbage(self):
        for case in pp.HARD_SUITE:
            with self.subTest(case=case.case_id):
                self.assertFalse(
                    case.validator("???this-is-not-a-valid-answer???"),
                    f"validator for {case.case_id} wrongly accepted garbage",
                )


class TestUsageTokens(unittest.TestCase):
    def test_openai_style(self):
        result = {"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}
        self.assertEqual(pp.usage_tokens(result), {"input": 10, "output": 5, "total": 15})

    def test_alt_naming(self):
        result = {"usage": {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}}
        self.assertEqual(pp.usage_tokens(result), {"input": 7, "output": 3, "total": 10})

    def test_total_falls_back_to_input_plus_output(self):
        result = {"usage": {"prompt_tokens": 7, "completion_tokens": 3}}
        self.assertEqual(pp.usage_tokens(result), {"input": 7, "output": 3, "total": 10})

    def test_missing_usage(self):
        self.assertEqual(pp.usage_tokens({}), {"input": 0, "output": 0, "total": 0})


class TestRedact(unittest.TestCase):
    def test_redacts_known_key(self):
        # The secret value must be gone. The exact marker may be overwritten by
        # the later JSON-field regex pass; we only care that nothing leaks.
        out = pp.redact('{"foo": "sk-12345678"}', "sk-12345678")
        self.assertNotIn("sk-12345678", out)
        self.assertIn("REDACTED", out)

    def test_redacts_sk_pattern(self):
        out = pp.redact("Bearer sk-abcdefghij", "")
        self.assertIn("sk-[REDACTED]", out)
        self.assertNotIn("abcdefghij", out)

    def test_redacts_json_field(self):
        out = pp.redact('{"Token": "secret-value-xyz"}', "")
        self.assertNotIn("secret-value-xyz", out)
        self.assertIn("[REDACTED]", out)


if __name__ == "__main__":
    unittest.main()
