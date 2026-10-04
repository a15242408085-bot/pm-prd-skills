import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "eval_summary", ROOT / "skills/pm-run-eval/scripts/summarize_eval.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.suite = json.loads((ROOT / "examples/rag-citations/suite.json").read_text())
        self.suite["gate"] = {"approved": True, "min_trial_pass_rate": 0.5}
        self.results = {
            "schema_version": "pm-prd-eval-results/v1",
            "suite_id": self.suite["suite_id"], "run_id": "test", "data_kind": "synthetic",
            "execution": copy.deepcopy(self.suite["execution"]),
            "records": [
                {"task_id": task["id"], "trial_index": trial, "status": "passed",
                 "transcript": "demo://transcript", "outcome": "demo://outcome"}
                for task in self.suite["tasks"]
                for trial in range(1, self.suite["trials_per_task"] + 1)
            ]
        }

    def test_all_pass(self):
        report = MODULE.summarize(self.suite, self.results)
        self.assertEqual(report["quality_gate"], "passed")
        self.assertEqual(report["scored_coverage"], 1)
        self.assertFalse(report["contains_real_execution_evidence"])

    def test_critical_failure_blocks_high_average(self):
        critical = next(task["id"] for task in self.suite["tasks"] if task["critical"])
        next(record for record in self.results["records"] if record["task_id"] == critical)["status"] = "failed"
        report = MODULE.summarize(self.suite, self.results)
        self.assertGreater(report["scored_trial_pass_rate"], 0.5)
        self.assertEqual(report["quality_gate"], "failed")

    def test_missing_trial_cannot_pass(self):
        self.results["records"].pop()
        report = MODULE.summarize(self.suite, self.results)
        self.assertEqual(report["quality_gate"], "incomplete")
        self.assertEqual(report["counts"]["missing"], 1)

    def test_environment_and_ungraded_are_incomplete(self):
        for index, status in enumerate(("infra_error", "ungraded")):
            self.results["records"][index].update(status=status, reason="runner not ready")
        report = MODULE.summarize(self.suite, self.results)
        self.assertEqual(report["quality_gate"], "incomplete")
        self.assertEqual(report["scored_trial_pass_rate"], 1)
        self.assertLess(report["scored_coverage"], 1)

    def test_unapproved_threshold_is_not_pass(self):
        self.suite["gate"]["approved"] = False
        self.assertEqual(MODULE.summarize(self.suite, self.results)["quality_gate"], "not_approved")

    def test_duplicate_trial_rejected(self):
        self.results["records"].append(copy.deepcopy(self.results["records"][0]))
        with self.assertRaises(MODULE.InputError):
            MODULE.summarize(self.suite, self.results)

    def test_version_mismatch_rejected(self):
        self.results["execution"]["prompt_version"] = "different"
        with self.assertRaises(MODULE.InputError):
            MODULE.summarize(self.suite, self.results)

    def test_pass_without_outcome_rejected(self):
        del self.results["records"][0]["outcome"]
        with self.assertRaises(MODULE.InputError):
            MODULE.summarize(self.suite, self.results)

    def test_real_cannot_use_demo_evidence(self):
        self.results["data_kind"] = "real"
        with self.assertRaises(MODULE.InputError):
            MODULE.summarize(self.suite, self.results)

    def test_empty_run_has_no_score_and_is_incomplete(self):
        self.results["records"] = []
        report = MODULE.summarize(self.suite, self.results)
        self.assertIsNone(report["scored_trial_pass_rate"])
        self.assertEqual(report["quality_gate"], "incomplete")

    def test_unknown_task_and_invalid_trial_rejected(self):
        for field, value in (("task_id", "UNKNOWN"), ("trial_index", 0), ("trial_index", True)):
            with self.subTest(field=field, value=value):
                results = copy.deepcopy(self.results)
                results["records"][0][field] = value
                with self.assertRaises(MODULE.InputError):
                    MODULE.summarize(self.suite, results)

    def test_noncritical_failure_uses_approved_threshold(self):
        noncritical = next(task["id"] for task in self.suite["tasks"] if not task["critical"])
        next(record for record in self.results["records"] if record["task_id"] == noncritical)["status"] = "failed"
        self.assertEqual(MODULE.summarize(self.suite, self.results)["quality_gate"], "passed")
        self.suite["gate"]["min_trial_pass_rate"] = 1
        self.assertEqual(MODULE.summarize(self.suite, self.results)["quality_gate"], "failed")


if __name__ == "__main__":
    unittest.main()
