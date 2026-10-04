#!/usr/bin/env python3
"""Check this pack's frontmatter, bundled resources and evaluation fixtures."""

import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if len(skills) != 11:
        errors.append(f"Expected 11 skills; found {len(skills)}")
    for path in skills:
        content = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\nname: ([a-z0-9]+(?:-[a-z0-9]+)*)\ndescription: ([^\n]+)\n---\n", content)
        if not match:
            errors.append(f"{path.relative_to(ROOT)}: invalid pack frontmatter")
            continue
        name, description = match.groups()
        if name != path.parent.name or len(name) > 64:
            errors.append(f"{name}: invalid name or directory mismatch")
        if not description.strip() or len(description) > 1024:
            errors.append(f"{name}: invalid description")
        if len(content.splitlines()) >= 500:
            errors.append(f"{name}: entrypoint too long")
        if "[TODO:" in content:
            errors.append(f"{name}: unfinished scaffold")
    for path in ROOT.rglob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            resource = (path.parent / target.split("#", 1)[0]).resolve()
            if not resource.is_relative_to(ROOT) or not resource.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing/outside resource {target}")
    module_path = ROOT / "skills/pm-run-eval/scripts/summarize_eval.py"
    spec = importlib.util.spec_from_file_location("eval_summary", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        example = ROOT / "examples/rag-citations"
        suite = json.loads((example / "suite.json").read_text(encoding="utf-8"))
        results = json.loads((example / "results-demo.json").read_text(encoding="utf-8"))
        module.summarize(suite, results)
        prd = (example / "prd.md").read_text(encoding="utf-8")
        for task in suite["tasks"]:
            for identifier in task["requirement_ids"] + task["acceptance_ids"]:
                if identifier not in prd:
                    errors.append(f"{task['id']}: unknown PRD identifier {identifier}")
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"Invalid evaluation fixture: {exc}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {len(skills)} skills, resource links, evaluation format and PRD traceability")
    return 0


if __name__ == "__main__":
    sys.exit(main())
