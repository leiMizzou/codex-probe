"""Tests for scoring, clustering, and comparison logic — all pure functions."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import provider_probe as pp


class TestNumericHelpers(unittest.TestCase):
    def test_median(self):
        self.assertIsNone(pp.median([]))
        self.assertEqual(pp.median([5]), 5.0)
        self.assertEqual(pp.median([1, 2, 3]), 2.0)
        self.assertEqual(pp.median([1, 2, 3, 4]), 2.5)

    def test_percentile(self):
        self.assertIsNone(pp.percentile([], 90))
        self.assertEqual(pp.percentile([10], 90), 10.0)
        # 10 values, p90 → between 9th (index 8) and 10th (index 9) with frac 0.1
        result = pp.percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 90)
        self.assertAlmostEqual(result, 9.1, places=2)

    def test_stats_empty(self):
        s = pp.stats([])
        for v in s.values():
            self.assertIsNone(v)

    def test_stats_basic(self):
        s = pp.stats([1, 2, 3, 4, 5])
        self.assertEqual(s["min"], 1.0)
        self.assertEqual(s["max"], 5.0)
        self.assertEqual(s["median"], 3.0)
        self.assertEqual(s["mean"], 3.0)

    def test_ratio(self):
        self.assertIsNone(pp.ratio(1, 0))
        self.assertEqual(pp.ratio(10, 4), 2.5)

    def test_nested_number(self):
        d = {"a": {"b": {"c": "3.14"}}}
        self.assertEqual(pp.nested_number(d, "a", "b", "c"), 3.14)
        self.assertIsNone(pp.nested_number(d, "a", "missing"))
        self.assertIsNone(pp.nested_number({"a": "not-a-number"}, "a"))


class TestClusterLogic(unittest.TestCase):
    def test_cluster_label_buckets_into_25(self):
        self.assertEqual(pp.cluster_label(0), "+0")
        self.assertEqual(pp.cluster_label(12), "+0")  # rounds to nearest 25 → 0
        self.assertEqual(pp.cluster_label(13), "+25")
        self.assertEqual(pp.cluster_label(335), "+325")
        self.assertEqual(pp.cluster_label(-50), "-50")

    def test_summarize_clusters_sorts_and_aggregates(self):
        overheads = [0, 0, 335, 335, 335]
        pass_by_cluster = {"+0": [True, True], "+325": [True, False, True]}
        clusters = pp.summarize_clusters(overheads, pass_by_cluster)
        self.assertEqual([c["cluster"] for c in clusters], ["+0", "+325"])
        self.assertEqual(clusters[0]["count"], 2)
        self.assertEqual(clusters[1]["count"], 3)
        self.assertEqual(clusters[1]["pass_rate"], round(2 / 3, 4))


class TestCompareFeatures(unittest.TestCase):
    def test_matching_features(self):
        probes = {
            "image_generation": {"ok": True, "image_returned": True},
            "snapshot_chat": {"ok": True},
            "model_retrieve": {"status": 200},
            "chat_json_schema": {"ok": True, "text": '{"verdict":"pass","score":10}'},
        }
        diff = pp.compare_features(probes, probes)
        self.assertFalse(diff["image_generation_differs"])
        self.assertFalse(diff["image_generation_gap"])
        self.assertFalse(diff["snapshot_differs"])
        self.assertFalse(diff["snapshot_gap"])
        self.assertFalse(diff["model_retrieve_gap"])
        self.assertEqual(diff["baseline_json_schema"], "conforms")
        self.assertFalse(diff["json_schema_differs"])

    def test_missing_image_feature_detected(self):
        baseline = {"image_generation": {"ok": True, "image_returned": True}}
        candidate = {"image_generation": {"ok": False, "status": 404}}
        diff = pp.compare_features(candidate, baseline)
        self.assertTrue(diff["image_generation_differs"])
        self.assertTrue(diff["image_generation_gap"])
        self.assertEqual(diff["baseline_image_generation"], "enabled")
        self.assertTrue(diff["candidate_image_generation"].startswith("blocked_or_failed:"))

    def test_extra_candidate_feature_is_difference_not_gap(self):
        baseline = {"image_generation": {"ok": False, "status": 403}}
        candidate = {"image_generation": {"ok": True, "image_returned": True}}
        diff = pp.compare_features(candidate, baseline)
        self.assertTrue(diff["image_generation_differs"])
        self.assertFalse(diff["image_generation_gap"])

    def test_json_schema_content_is_validated(self):
        baseline = {"chat_json_schema": {"ok": True, "text": '{"verdict":"pass","score":10}'}}
        candidate = {"chat_json_schema": {"ok": True, "text": '{"verdict":"insufficient_information","score":0}'}}
        diff = pp.compare_features(candidate, baseline)
        self.assertEqual(diff["baseline_json_schema"], "conforms")
        self.assertEqual(diff["candidate_json_schema"], "nonconforming:verdict_out_of_enum")
        self.assertTrue(diff["json_schema_gap"])


class TestCompareSpeed(unittest.TestCase):
    def test_speed_ratios(self):
        baseline = {
            "summary": {
                "speed": {
                    "latency_s": {"median": 2.0, "p90": 3.0},
                    "output_tokens_per_s": {"median": 100.0},
                    "total_tokens_per_s": {"median": 150.0},
                }
            }
        }
        candidate = {
            "summary": {
                "speed": {
                    "latency_s": {"median": 4.0, "p90": 6.0},
                    "output_tokens_per_s": {"median": 50.0},
                    "total_tokens_per_s": {"median": 75.0},
                }
            }
        }
        speed = pp.compare_speed(candidate, baseline)
        self.assertEqual(speed["median_latency_ratio"], 2.0)
        self.assertEqual(speed["p90_latency_ratio"], 2.0)
        self.assertEqual(speed["output_tokens_per_s_ratio"], 0.5)


class TestScoreCandidate(unittest.TestCase):
    def _baseline(self, pass_rate=1.0):
        return {"summary": {"pass_rate": pass_rate}}

    def _candidate(self, pass_rate=1.0):
        return {"summary": {"pass_rate": pass_rate}}

    def test_perfect_match_gives_low_risk(self):
        scores = pp.score_candidate(
            candidate=self._candidate(1.0),
            baseline=self._baseline(1.0),
            clusters=[{"cluster": "+0", "median_delta_input_tokens": 0, "pass_rate": 1.0}],
            feature_diff={"image_generation_gap": False, "snapshot_gap": False, "model_retrieve_gap": False,
                          "baseline_model_retrieve_status": 200, "candidate_model_retrieve_status": 200},
            quality_delta=0.0,
            input_ratio=1.0,
            total_ratio=1.0,
            speed_comparison={"median_latency_ratio": 1.0, "p90_latency_ratio": 1.0, "output_tokens_per_s_ratio": 1.0},
        )
        self.assertEqual(scores["quality_score"], 100)
        self.assertEqual(scores["wrapper_or_routing_suspicion"], 0)
        self.assertEqual(scores["billing_overhead_suspicion"], 0)
        self.assertEqual(scores["overall_risk"], 0.0)

    def test_two_tier_input_clusters_raise_wrapper_score(self):
        # +0 and +335 tier, both passing → wrapper suspicion
        scores = pp.score_candidate(
            candidate=self._candidate(1.0),
            baseline=self._baseline(1.0),
            clusters=[
                {"cluster": "+0", "median_delta_input_tokens": 0, "pass_rate": 1.0},
                {"cluster": "+325", "median_delta_input_tokens": 335, "pass_rate": 1.0},
            ],
            feature_diff={"image_generation_gap": False, "snapshot_gap": False, "model_retrieve_gap": False,
                          "baseline_model_retrieve_status": 200, "candidate_model_retrieve_status": 200},
            quality_delta=0.0,
            input_ratio=1.0,
            total_ratio=1.0,
            speed_comparison={"median_latency_ratio": 1.0, "p90_latency_ratio": 1.0, "output_tokens_per_s_ratio": 1.0},
        )
        self.assertGreaterEqual(scores["wrapper_or_routing_suspicion"], 70)

    def test_token_inflation_raises_billing_score(self):
        scores = pp.score_candidate(
            candidate=self._candidate(1.0),
            baseline=self._baseline(1.0),
            clusters=[{"cluster": "+0", "median_delta_input_tokens": 0, "pass_rate": 1.0}],
            feature_diff={"image_generation_gap": False, "snapshot_gap": False, "model_retrieve_gap": False,
                          "baseline_model_retrieve_status": 200, "candidate_model_retrieve_status": 200},
            quality_delta=0.0,
            input_ratio=4.0,
            total_ratio=2.5,
            speed_comparison={"median_latency_ratio": 1.0, "p90_latency_ratio": 1.0, "output_tokens_per_s_ratio": 1.0},
        )
        self.assertGreater(scores["billing_overhead_suspicion"], 50)

    def test_quality_drop_raises_substitution_and_drops_quality(self):
        scores = pp.score_candidate(
            candidate=self._candidate(0.7),
            baseline=self._baseline(1.0),
            clusters=[{"cluster": "+0", "median_delta_input_tokens": 0, "pass_rate": 0.7}],
            feature_diff={"image_generation_gap": False, "snapshot_gap": False, "model_retrieve_gap": False,
                          "baseline_model_retrieve_status": 200, "candidate_model_retrieve_status": 200},
            quality_delta=-0.3,
            input_ratio=1.0,
            total_ratio=1.0,
            speed_comparison={"median_latency_ratio": 1.0, "p90_latency_ratio": 1.0, "output_tokens_per_s_ratio": 1.0},
        )
        self.assertLess(scores["quality_score"], 60)
        self.assertGreater(scores["model_substitution_suspicion"], 30)

    def test_missing_image_feature_raises_feature_score(self):
        scores = pp.score_candidate(
            candidate=self._candidate(1.0),
            baseline=self._baseline(1.0),
            clusters=[{"cluster": "+0", "median_delta_input_tokens": 0, "pass_rate": 1.0}],
            feature_diff={"image_generation_gap": True, "snapshot_gap": True, "model_retrieve_gap": True,
                          "baseline_model_retrieve_status": 200, "candidate_model_retrieve_status": 404},
            quality_delta=0.0,
            input_ratio=1.0,
            total_ratio=1.0,
            speed_comparison={"median_latency_ratio": 1.0, "p90_latency_ratio": 1.0, "output_tokens_per_s_ratio": 1.0},
        )
        # 35 (image) + 20 (snapshot) + 10 (model_retrieve diff) = 65
        self.assertEqual(scores["feature_gap_suspicion"], 65)

    def test_slow_candidate_raises_speed_score(self):
        scores = pp.score_candidate(
            candidate=self._candidate(1.0),
            baseline=self._baseline(1.0),
            clusters=[{"cluster": "+0", "median_delta_input_tokens": 0, "pass_rate": 1.0}],
            feature_diff={"image_generation_gap": False, "snapshot_gap": False, "model_retrieve_gap": False,
                          "baseline_model_retrieve_status": 200, "candidate_model_retrieve_status": 200},
            quality_delta=0.0,
            input_ratio=1.0,
            total_ratio=1.0,
            speed_comparison={"median_latency_ratio": 3.0, "p90_latency_ratio": 3.5, "output_tokens_per_s_ratio": 0.4},
        )
        self.assertGreater(scores["speed_suspicion"], 50)

    def test_json_schema_gap_raises_feature_score(self):
        scores = pp.score_candidate(
            candidate=self._candidate(1.0),
            baseline=self._baseline(1.0),
            clusters=[{"cluster": "+0", "median_delta_input_tokens": 0, "pass_rate": 1.0}],
            feature_diff={"image_generation_gap": False, "snapshot_gap": False, "json_schema_gap": True, "model_retrieve_gap": False,
                          "baseline_model_retrieve_status": 200, "candidate_model_retrieve_status": 200},
            quality_delta=0.0,
            input_ratio=1.0,
            total_ratio=1.0,
            speed_comparison={"median_latency_ratio": 1.0, "p90_latency_ratio": 1.0, "output_tokens_per_s_ratio": 1.0},
        )
        self.assertEqual(scores["feature_gap_suspicion"], 15)


class TestCostEstimation(unittest.TestCase):
    def test_no_runs(self):
        self.assertEqual(pp.estimate_cost([]), {"available": False})

    def test_known_model(self):
        runs = [{"model": "gpt-5.5", "tokens": {"input": 1_000_000, "output": 1_000_000}}]
        result = pp.estimate_cost(runs)
        self.assertTrue(result["available"])
        # 5.0 input + 30.0 output per 1M
        self.assertAlmostEqual(result["estimated_cost_usd"], 35.0, places=4)

    def test_unknown_model_returns_helpful_reason(self):
        runs = [{"model": "gpt-mystery", "tokens": {"input": 100, "output": 50}}]
        result = pp.estimate_cost(runs)
        self.assertFalse(result["available"])
        self.assertIn("--prices-file", result["reason"])
        self.assertIn("gpt-mystery", result["reason"])

    def test_uses_first_non_empty_model_or_provider_model(self):
        prices = {"gpt-x": {"input": 2.0, "output": 4.0}}
        runs = [
            {"model": "", "tokens": {"input": 500_000, "output": 0}},
            {"model": "gpt-x", "tokens": {"input": 0, "output": 500_000}},
        ]
        result = pp.estimate_cost(runs, prices)
        self.assertTrue(result["available"])
        self.assertEqual(result["model"], "gpt-x")
        self.assertAlmostEqual(result["estimated_cost_usd"], 3.0, places=4)

        result = pp.estimate_cost([{"tokens": {"input": 1_000_000, "output": 0}}], prices, "gpt-x")
        self.assertTrue(result["available"])
        self.assertAlmostEqual(result["estimated_cost_usd"], 2.0, places=4)

    def test_cost_ratio_handles_missing(self):
        self.assertIsNone(pp.cost_ratio({"available": False}, {"available": True, "estimated_cost_usd": 10}))
        self.assertEqual(
            pp.cost_ratio({"available": True, "estimated_cost_usd": 20}, {"available": True, "estimated_cost_usd": 10}),
            2.0,
        )


class TestPricesFileLoader(unittest.TestCase):
    def _write(self, payload: object) -> str:
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(payload, f)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_empty_path_returns_empty(self):
        self.assertEqual(pp._load_prices_file(""), {})

    def test_valid_file(self):
        path = self._write({"gpt-x": {"input": 1.5, "output": 4.0}})
        self.assertEqual(pp._load_prices_file(path), {"gpt-x": {"input": 1.5, "output": 4.0}})

    def test_missing_keys_rejected(self):
        path = self._write({"gpt-x": {"input": 1.5}})
        with self.assertRaises(SystemExit):
            pp._load_prices_file(path)

    def test_non_numeric_rejected(self):
        path = self._write({"gpt-x": {"input": "free", "output": 0.0}})
        with self.assertRaises(SystemExit):
            pp._load_prices_file(path)

    def test_non_object_root_rejected(self):
        path = self._write(["not", "an", "object"])
        with self.assertRaises(SystemExit):
            pp._load_prices_file(path)


class TestJsonOutput(unittest.TestCase):
    def test_save_json_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nested", "report.json")
            pp.save_json(path, {"ok": True})
            with open(path, "r", encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"ok": True})


class TestCompareProfile(unittest.TestCase):
    def _scores(self):
        return {"wrapper_or_routing_suspicion": 0, "feature_gap_suspicion": 0, "model_substitution_suspicion": 0}

    def test_no_profile_in_baseline(self):
        result = pp.compare_profile({}, 0.0, 1.0, 1.0, {}, self._scores())
        self.assertEqual(result["verdict"], "unknown")
        self.assertIsNone(result["baseline_profile"])

    def test_close_match_high_confidence(self):
        baseline = {"meta": {"profile": "codex-fast"}}
        result = pp.compare_profile(
            baseline, quality_delta=0.0, input_ratio=1.0, total_ratio=1.0,
            speed_comparison={"median_latency_ratio": 1.0, "p90_latency_ratio": 1.0, "output_tokens_per_s_ratio": 1.0},
            scores=self._scores(),
        )
        self.assertEqual(result["verdict"], "matches_baseline_profile")
        self.assertGreaterEqual(result["confidence"], 80)

    def test_bad_match_unlikely(self):
        baseline = {"meta": {"profile": "codex-fast"}}
        result = pp.compare_profile(
            baseline, quality_delta=-0.2, input_ratio=4.0, total_ratio=3.0,
            speed_comparison={"median_latency_ratio": 3.0, "p90_latency_ratio": 4.0, "output_tokens_per_s_ratio": 0.3},
            scores={"wrapper_or_routing_suspicion": 70, "feature_gap_suspicion": 55, "model_substitution_suspicion": 40},
        )
        self.assertEqual(result["verdict"], "unlikely_match")
        self.assertLess(result["confidence"], 60)


class TestAssessment(unittest.TestCase):
    CLEAN_FEATURE_DIFF = {
        "image_generation_gap": False,
        "snapshot_gap": False,
        "json_schema_gap": False,
        "model_retrieve_gap": False,
    }
    CLEAN_SCORES = {
        "overall_risk": 0,
        "model_substitution_suspicion": 0,
        "wrapper_or_routing_suspicion": 0,
        "billing_overhead_suspicion": 0,
        "feature_gap_suspicion": 0,
        "speed_suspicion": 0,
    }

    def _assess(self, **overrides):
        defaults = dict(
            baseline_pass_rate=1.0,
            candidate_pass_rate=1.0,
            quality_delta=0.0,
            input_ratio=1.0,
            total_ratio=1.0,
            speed_comparison={"median_latency_ratio": 1.0},
            feature_diff=dict(self.CLEAN_FEATURE_DIFF),
            scores=dict(self.CLEAN_SCORES),
            model="gpt-5.5",
        )
        defaults.update(overrides)
        return pp.assess_result(**defaults)

    def test_clean_text_candidate_is_usable(self):
        result = self._assess()
        self.assertEqual(result["verdict"], "passes_text_quality_with_caveats")
        self.assertEqual(result["risk_level"], "low")
        self.assertTrue(result["quality_gate_passed"])
        self.assertEqual(result["suitability"], "usable_for_gpt_5_5_text")
        self.assertIn("gpt-5.5 text workloads similar to this hard suite", result["recommended_use"])
        self.assertIn("no feature gaps versus the baseline", result["strengths"])

    def test_quality_pass_with_provider_differences_is_called_out(self):
        result = self._assess(
            input_ratio=3.5,
            total_ratio=2.0,
            feature_diff={
                "image_generation_gap": True,
                "snapshot_gap": True,
                "json_schema_gap": False,
                "model_retrieve_gap": False,
            },
            scores={
                "overall_risk": 55,
                "model_substitution_suspicion": 0,
                "wrapper_or_routing_suspicion": 70,
                "billing_overhead_suspicion": 89,
                "feature_gap_suspicion": 55,
                "speed_suspicion": 0,
            },
        )
        self.assertEqual(result["verdict"], "passes_text_quality_but_provider_differs")
        self.assertEqual(result["risk_level"], "high")
        self.assertIn("stable wrapper/routing token overhead", result["primary_issues"])
        self.assertIn("material token/cost overhead", result["primary_issues"])
        self.assertIn("missing or different features vs baseline", result["primary_issues"])
        self.assertIn("workflows requiring missing baseline features", result["avoid_use"])
        self.assertNotIn("no feature gaps versus the baseline", result["strengths"])

    def test_substitution_signal_triggers_possible_issue_verdict(self):
        result = self._assess(
            baseline_pass_rate=1.0,
            candidate_pass_rate=0.92,  # passes 0.9 gate but not the 0.97 quality_gate
            quality_delta=-0.08,
            scores={**self.CLEAN_SCORES, "overall_risk": 30, "model_substitution_suspicion": 50},
        )
        self.assertEqual(result["verdict"], "possible_substitution_or_quality_issue")
        self.assertEqual(result["suitability"], "limited_use_with_manual_review")
        self.assertFalse(result["quality_gate_passed"])
        self.assertIn("possible model substitution", result["primary_issues"])

    def test_severe_quality_drop_fails_gate(self):
        result = self._assess(
            candidate_pass_rate=0.5,
            quality_delta=-0.5,
            scores={**self.CLEAN_SCORES, "overall_risk": 30, "model_substitution_suspicion": 0},
        )
        self.assertEqual(result["verdict"], "fails_quality_gate")
        self.assertEqual(result["suitability"], "not_recommended")
        self.assertIn("high-stakes workloads without a stronger trusted baseline and more repeats", result["avoid_use"])

    def test_speed_regression_listed_in_avoid_use(self):
        result = self._assess(scores={**self.CLEAN_SCORES, "speed_suspicion": 60, "overall_risk": 25})
        self.assertIn("material speed regression", result["primary_issues"])
        self.assertIn("latency-sensitive production paths", result["avoid_use"])

    def test_model_slug_is_sanitized(self):
        result = self._assess(model="GPT-5.6/Codex-Spark!")
        # Lowercased, runs of non-alnum collapse to single underscore, strip edges
        self.assertEqual(result["suitability"], "usable_for_gpt_5_6_codex_spark_text")
        self.assertIn("GPT-5.6/Codex-Spark! text workloads similar to this hard suite", result["recommended_use"])

    def test_empty_model_falls_back_to_generic_label(self):
        result = self._assess(model="")
        self.assertEqual(result["suitability"], "usable_for_text_workloads")
        self.assertIn("this model text workloads similar to this hard suite", result["recommended_use"])

    def test_plain_language_picks_up_issues(self):
        result = self._assess(
            input_ratio=3.5,
            scores={**self.CLEAN_SCORES, "overall_risk": 55, "billing_overhead_suspicion": 70},
        )
        # provider_differs branch should mention the risk level and at least one issue
        self.assertIn("high", result["plain_language"])
        self.assertIn("material token/cost overhead", result["plain_language"])


class TestRiskLevel(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(pp.risk_level(0), "low")
        self.assertEqual(pp.risk_level(19.99), "low")
        self.assertEqual(pp.risk_level(20), "moderate")
        self.assertEqual(pp.risk_level(44.99), "moderate")
        self.assertEqual(pp.risk_level(45), "high")
        self.assertEqual(pp.risk_level(69.99), "high")
        self.assertEqual(pp.risk_level(70), "critical")
        self.assertEqual(pp.risk_level(100), "critical")


class TestProbeSchemaValidator(unittest.TestCase):
    def test_well_formed(self):
        ok, reason = pp._validate_probe_schema_text('{"verdict":"pass","score":10}')
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_invalid_json(self):
        ok, reason = pp._validate_probe_schema_text("not json")
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("invalid_json:"))

    def test_not_object(self):
        ok, reason = pp._validate_probe_schema_text("[1,2,3]")
        self.assertFalse(ok)
        self.assertEqual(reason, "not_object")

    def test_unexpected_keys(self):
        ok, reason = pp._validate_probe_schema_text('{"verdict":"pass","score":5,"extra":true}')
        self.assertFalse(ok)
        self.assertEqual(reason, "unexpected_keys")

    def test_verdict_out_of_enum(self):
        ok, reason = pp._validate_probe_schema_text('{"verdict":"insufficient","score":5}')
        self.assertFalse(ok)
        self.assertEqual(reason, "verdict_out_of_enum")

    def test_score_not_integer(self):
        ok, reason = pp._validate_probe_schema_text('{"verdict":"pass","score":3.5}')
        self.assertFalse(ok)
        self.assertEqual(reason, "score_not_integer")

    def test_score_is_bool_rejected(self):
        # bool is a subclass of int — make sure we explicitly reject it
        ok, reason = pp._validate_probe_schema_text('{"verdict":"pass","score":true}')
        self.assertFalse(ok)
        self.assertEqual(reason, "score_not_integer")

    def test_score_out_of_range(self):
        ok, reason = pp._validate_probe_schema_text('{"verdict":"pass","score":11}')
        self.assertFalse(ok)
        self.assertEqual(reason, "score_out_of_range")


if __name__ == "__main__":
    unittest.main()
