#!/usr/bin/env python3
"""Validate and summarize recorded trials. Does not execute models or graders."""

import argparse
import json
import math
import sys
from pathlib import Path


VERSIONS = ("model_version", "prompt_version", "tool_version", "data_version")
STATUSES = ("passed", "failed", "infra_error", "ungraded")


class InputError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InputError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    return isinstance(value, list) and bool(value) and all(nonempty(x) for x in value)


def check_execution(value):
    require(isinstance(value, dict), "execution must be an object")
    for key in VERSIONS:
        require(nonempty(value.get(key)), f"execution.{key} must be nonempty")


def validate_suite(suite):
    require(isinstance(suite, dict), "suite must be an object")
    require(suite.get("schema_version") == "pm-prd-eval/v1", "unsupported suite schema")
    require(nonempty(suite.get("suite_id")), "suite_id must be nonempty")
    require(suite.get("purpose") in ("capability", "regression"), "invalid purpose")
    check_execution(suite.get("execution"))
    k = suite.get("trials_per_task")
    require(type(k) is int and k > 0, "trials_per_task must be a positive integer")
    gate = suite.get("gate")
    require(isinstance(gate, dict), "gate must be an object")
    require(type(gate.get("approved")) is bool, "gate.approved must be boolean")
    threshold = gate.get("min_trial_pass_rate")
    require(type(threshold) in (int, float) and math.isfinite(threshold)
            and 0 <= threshold <= 1, "min_trial_pass_rate must be a finite ratio in [0,1]")
    tasks = suite.get("tasks")
    require(isinstance(tasks, list) and bool(tasks), "tasks must be a nonempty list")
    seen = set()
    for task in tasks:
        require(isinstance(task, dict), "each task must be an object")
        task_id = task.get("id")
        require(nonempty(task_id), "task id must be nonempty")
        require(task_id not in seen, f"duplicate task id: {task_id}")
        seen.add(task_id)
        require(task.get("source_type") in ("real", "synthetic"), f"{task_id}: invalid source_type")
        require(type(task.get("critical")) is bool, f"{task_id}: critical must be boolean")
        for key in ("requirement_ids", "acceptance_ids"):
            require(strings(task.get(key)), f"{task_id}: {key} must be nonempty string array")
        for key in ("input", "environment", "expected"):
            require(nonempty(task.get(key)), f"{task_id}: {key} must be nonempty")
        forbidden = task.get("forbidden")
        require(isinstance(forbidden, list) and all(nonempty(x) for x in forbidden),
                f"{task_id}: forbidden must be a string array")
        grader = task.get("grader")
        require(isinstance(grader, dict), f"{task_id}: grader must be an object")
        require(grader.get("type") in ("code", "model", "human", "hybrid"),
                f"{task_id}: invalid grader type")
        require(nonempty(grader.get("criteria")), f"{task_id}: grader criteria required")
    return suite


def summarize(suite, results):
    validate_suite(suite)
    require(isinstance(results, dict), "results must be an object")
    require(results.get("schema_version") == "pm-prd-eval-results/v1", "unsupported result schema")
    require(results.get("suite_id") == suite["suite_id"], "suite_id mismatch")
    require(nonempty(results.get("run_id")), "run_id must be nonempty")
    kind = results.get("data_kind")
    require(kind in ("real", "synthetic"), "data_kind must be real or synthetic")
    check_execution(results.get("execution"))
    for key in VERSIONS:
        require(results["execution"][key] == suite["execution"][key], f"version mismatch: {key}")
        if kind == "real":
            value = results["execution"][key].casefold()
            require(not any(x in value for x in ("待确定", "待确认", "unknown", "todo", "tbd")),
                    f"real run requires a fixed {key}")
    records = results.get("records")
    require(isinstance(records, list), "records must be a list")
    k = suite["trials_per_task"]
    rows = {
        task["id"]: {"task_id": task["id"], "critical": task["critical"],
                     **{status: 0 for status in STATUSES}, "missing": k}
        for task in suite["tasks"]
    }
    seen = set()
    critical_failures = []
    incomplete_trials = []
    for record in records:
        require(isinstance(record, dict), "record must be an object")
        task_id = record.get("task_id")
        require(nonempty(task_id) and task_id in rows, "unknown task_id")
        trial = record.get("trial_index")
        require(type(trial) is int and 1 <= trial <= k, f"{task_id}: invalid trial_index")
        pair = (task_id, trial)
        require(pair not in seen, f"duplicate trial: {task_id}/{trial}")
        seen.add(pair)
        status = record.get("status")
        require(status in STATUSES, f"{task_id}/{trial}: invalid status")
        if status in ("passed", "failed"):
            for key in ("transcript", "outcome"):
                require(nonempty(record.get(key)), f"{task_id}/{trial}: missing {key} evidence")
                if kind == "real":
                    require(not record[key].startswith("demo://"), "demo evidence cannot support a real run")
        else:
            require(nonempty(record.get("reason")), f"{task_id}/{trial}: error/ungraded reason required")
            incomplete_trials.append({"task_id": task_id, "trial_index": trial,
                                      "status": status, "reason": record["reason"]})
        row = rows[task_id]
        row[status] += 1
        row["missing"] -= 1
        if row["critical"] and status == "failed":
            critical_failures.append({"task_id": task_id, "trial_index": trial})
    for task_id in rows:
        for trial in range(1, k + 1):
            if (task_id, trial) not in seen:
                incomplete_trials.append({"task_id": task_id, "trial_index": trial, "status": "missing"})
    totals = {status: sum(row[status] for row in rows.values())
              for status in (*STATUSES, "missing")}
    planned = len(rows) * k
    scored = totals["passed"] + totals["failed"]
    rate = totals["passed"] / scored if scored else None
    complete = scored == planned
    if critical_failures:
        quality_gate = "failed"
    elif not complete:
        quality_gate = "incomplete"
    elif not suite["gate"]["approved"]:
        quality_gate = "not_approved"
    elif rate >= suite["gate"]["min_trial_pass_rate"]:
        quality_gate = "passed"
    else:
        quality_gate = "failed"
    return {
        "suite_id": suite["suite_id"], "run_id": results["run_id"], "data_kind": kind,
        "execution": results["execution"], "planned_trials": planned, "scored_trials": scored,
        "counts": totals, "scored_trial_pass_rate": rate,
        "scored_coverage": scored / planned, "completion": "complete" if complete else "incomplete",
        "quality_gate": quality_gate, "gate_approved": suite["gate"]["approved"],
        "contains_real_execution_evidence": kind == "real",
        "critical_failures": critical_failures, "incomplete_trials": incomplete_trials,
        "tasks": list(rows.values()),
        "note": "Summarizes supplied records only; evidence must be independently checked. Does not approve a launch."
    }


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--results", required=True)
    args = parser.parse_args()
    try:
        report = summarize(load_json(args.suite), load_json(args.results))
    except (OSError, ValueError, TypeError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
