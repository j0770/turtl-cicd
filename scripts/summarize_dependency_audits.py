"""Summarize scanner output without claiming exploitability or accepting findings."""

import argparse
import json
from pathlib import Path


def summarize_npm(report, lock):
    if (
        not isinstance(report, dict)
        or "error" in report
        or not isinstance(report.get("vulnerabilities"), dict)
    ):
        raise ValueError("npm did not return a complete vulnerability report")
    findings = []
    for name, item in sorted(report["vulnerabilities"].items()):
        nodes = []
        for node in item.get("nodes", []):
            package = lock.get("packages", {}).get(node)
            if package is None:
                raise ValueError(f"npm node missing from lockfile: {node}")
            nodes.append(
                {
                    "path": node,
                    "version": package.get("version"),
                    "dev": package.get("dev", False),
                    "optional": package.get("optional", False),
                }
            )
        findings.append(
            {
                "package": name,
                "direct": item.get("isDirect"),
                "severity": item.get("severity"),
                "range": item.get("range"),
                "instances": nodes,
                "via": item.get("via", []),
                "fix_available": item.get("fixAvailable", False),
            }
        )
    return {
        "scanner": "npm audit",
        "status": "findings" if findings else "clean",
        "affected_packages": len(findings),
        "reported_package_counts_by_severity": report.get("metadata", {}).get(
            "vulnerabilities", {}
        ),
        "findings": findings,
    }


def summarize_python(report):
    if not isinstance(report, dict) or not isinstance(report.get("dependencies"), list):
        raise ValueError("pip-audit did not return a complete dependency report")
    skipped = [d for d in report["dependencies"] if d.get("skip_reason")]
    findings = [
        {"package": d["name"], "version": d["version"], "vulnerabilities": d["vulns"]}
        for d in report["dependencies"]
        if d.get("vulns")
    ]
    return {
        "scanner": "pip-audit",
        "status": "error" if skipped else "findings" if findings else "clean",
        "affected_packages": len(findings),
        "package_advisory_pairs": sum(len(d["vulnerabilities"]) for d in findings),
        "unique_advisory_ids": sorted(
            {v["id"] for d in findings for v in d["vulnerabilities"]}
        ),
        "skipped_dependencies": skipped,
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--npm-report", type=Path)
    parser.add_argument("--npm-lock", type=Path)
    parser.add_argument("--python-report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (args.npm_report or args.python_report):
        parser.error("at least one report is required")
    result = {
        "schema_version": 1,
        "exploitability_assessed": False,
        "findings_accepted": False,
        "reports": {},
    }
    for kind, path in [("npm", args.npm_report), ("python", args.python_report)]:
        if path is None:
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8-sig"))
            if kind == "npm":
                if args.npm_lock is None:
                    raise ValueError("npm lockfile is required")
                lock = json.loads(args.npm_lock.read_text(encoding="utf-8-sig"))
                result["reports"][kind] = summarize_npm(report, lock)
            else:
                result["reports"][kind] = summarize_python(report)
        except (OSError, ValueError, KeyError, TypeError) as error:
            result["reports"][kind] = {"status": "error", "detail": str(error)}
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    statuses = {r["status"] for r in result["reports"].values()}
    return 2 if "error" in statuses else 1 if "findings" in statuses else 0


if __name__ == "__main__":
    raise SystemExit(main())
