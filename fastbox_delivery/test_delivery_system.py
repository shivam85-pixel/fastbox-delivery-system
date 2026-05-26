"""
test_delivery_system.py
=======================
Automated test runner for the FastBox Delivery System.

Runs every test case in the 'test_cases/' directory and the base_case.json,
validates key invariants, and prints a pass/fail summary.

Invariants checked per test case:
  1. Total packages_delivered across all agents == len(input packages)
  2. best_agent exists in the agent list
  3. efficiency == total_distance / packages_delivered (within float tolerance)
  4. Agents with 0 packages have efficiency == null
  5. best_agent has the minimum efficiency among eligible agents
"""

import json
import math
import sys
from pathlib import Path

# Allow importing from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from delivery_system import run, load_data


TOLERANCE = 1e-1   # allow ±0.1 rounding difference after round(x, 2)

PASS = "✓"
FAIL = "✗"


def check_report(data: dict, report: dict) -> list:
    """
    Validate a report against the source data.
    Returns a list of error strings (empty = all passed).
    """
    errors = []
    packages  = data["packages"]
    agent_ids = set(data["agents"].keys())

    # 1. Total delivered == total packages
    total_delivered = sum(
        v["packages_delivered"] for k, v in report.items() if k != "best_agent"
    )
    if total_delivered != len(packages):
        errors.append(
            f"delivered sum {total_delivered} ≠ package count {len(packages)}"
        )

    # 2. best_agent is valid
    best = report.get("best_agent")
    if best is not None and best not in agent_ids:
        errors.append(f"best_agent '{best}' not in agents {agent_ids}")

    for aid in agent_ids:
        stats = report.get(aid, {})
        n    = stats.get("packages_delivered", 0)
        dist = stats.get("total_distance", 0.0)
        eff  = stats.get("efficiency")

        # 3. efficiency consistency
        if n > 0:
            expected_eff = round(dist / n, 2)
            if eff is None or abs(eff - expected_eff) > TOLERANCE:
                errors.append(
                    f"{aid}: efficiency {eff} ≠ expected {expected_eff}"
                )
        # 4. zero-package agents have null efficiency
        else:
            if eff is not None:
                errors.append(
                    f"{aid}: 0 packages but efficiency={eff} (expected null)"
                )

    # 5. best_agent has minimum efficiency
    eligible = {
        k: v["efficiency"]
        for k, v in report.items()
        if k != "best_agent" and v.get("efficiency") is not None
    }
    if eligible:
        min_eff = min(eligible.values())
        if best is not None and eligible.get(best) != min_eff:
            errors.append(
                f"best_agent '{best}' has efficiency {eligible.get(best)}, "
                f"but min is {min_eff}"
            )

    return errors


def run_test(label: str, input_path: Path) -> bool:
    """Run one test case. Returns True if all checks pass."""
    try:
        data   = load_data(input_path)
        report = run(
            input_path,
            report_path  = f"/tmp/report_{label}.json",
            csv_path     = f"/tmp/top_{label}.csv",
            print_ascii  = False,
            print_delays = False,
        )
        errors = check_report(data, report)
        if errors:
            print(f"  [{FAIL}] {label}")
            for e in errors:
                print(f"        → {e}")
            return False
        else:
            pkgs = sum(v["packages_delivered"] for k, v in report.items() if k != "best_agent")
            print(f"  [{PASS}] {label}  "
                  f"packages={pkgs}  best={report['best_agent']}")
            return True
    except Exception as exc:
        print(f"  [{FAIL}] {label}  EXCEPTION: {exc}")
        import traceback; traceback.print_exc()
        return False


def main():
    base_dir   = Path(__file__).parent
    test_dir   = base_dir / "test_cases"
    base_case  = base_dir / "data" / "base_case.json"

    test_files = sorted(test_dir.glob("test_case_*.json"))
    all_files  = ([base_case] if base_case.exists() else []) + test_files

    print("\n" + "="*55)
    print("  FastBox Delivery System — Test Suite")
    print("="*55)

    passed = 0
    total  = len(all_files)

    for path in all_files:
        label = path.stem
        ok = run_test(label, path)
        if ok:
            passed += 1

    print("\n" + "="*55)
    print(f"  Results: {passed}/{total} tests passed")
    print("="*55 + "\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
