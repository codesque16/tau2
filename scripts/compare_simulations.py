#!/usr/bin/env python3
"""
Compare two simulation result JSON files: outcomes per task, divergence (one fails other passes), and failure reasons.
"""
import json
import sys
from pathlib import Path


def load_results(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def get_task_purpose(tasks: list, task_id: str) -> str:
    for t in tasks:
        if t.get("id") == task_id:
            d = t.get("description") or {}
            return (d.get("purpose") or "")[:120]
    return ""


def summarize_failure(reward_info: dict) -> str:
    if not reward_info or reward_info.get("reward", 1) == 1.0:
        return ""
    reasons = []
    rb = reward_info.get("reward_breakdown") or {}
    db = reward_info.get("db_check") or {}
    if rb.get("DB") == 0.0 or db.get("db_match") is False:
        reasons.append("DB mismatch (wrong/forbidden action or state)")
    if rb.get("COMMUNICATE") == 0.0:
        for check in (reward_info.get("nl_assertions") or []):
            if check.get("met") is False:
                reasons.append(f"NL: {check.get('nl_assertion', '')[:80]}")
        for check in (reward_info.get("communicate_checks") or []):
            if check.get("met") is False:
                reasons.append(f"Comm: {check.get('info', '')[:80]}")
        action_checks = reward_info.get("action_checks") or []
        failed_actions = [a for a in action_checks if a.get("action_match") is False]
        if failed_actions:
            for a in failed_actions:
                act = a.get("action") or {}
                reasons.append(f"Action not done/ wrong: {act.get('name', '')} {act.get('arguments', {})}")
    return "; ".join(reasons) if reasons else "COMMUNICATE/other"


def build_task_outcomes(data: dict) -> dict:
    """task_id -> {reward, failure_reason, purpose}."""
    tasks = {t["id"]: t for t in data.get("tasks", [])}
    out = {}
    for sim in data.get("simulations", []):
        tid = sim.get("task_id")
        if tid is None:
            continue
        ri = sim.get("reward_info") or {}
        reward = ri.get("reward", 0.0)
        out[tid] = {
            "reward": reward,
            "failure_reason": summarize_failure(ri) if reward == 0.0 else "",
            "purpose": get_task_purpose(data.get("tasks", []), tid),
        }
    return out


def main():
    base = Path(__file__).resolve().parent.parent
    path1 = base / "data/simulations/2026-02-18T14:41:30.634797_airline_llm_agent_gemini-3-flash-preview_user_simulator_gemini-3-flash-preview.json"
    path2 = base / "data/simulations/2026-02-18T13:18:52.904173_airline_llm_agent_gemini-3-flash-preview_user_simulator_gemini-3-flash-preview.json"
    if len(sys.argv) >= 3:
        path1, path2 = Path(sys.argv[1]), Path(sys.argv[2])
    path1, path2 = Path(path1), Path(path2)
    if not path1.exists() or not path2.exists():
        print("Files not found:", path1, path2)
        sys.exit(1)

    d1 = load_results(path1)
    d2 = load_results(path2)
    o1 = build_task_outcomes(d1)
    o2 = build_task_outcomes(d2)
    all_ids = sorted(set(o1) | set(o2), key=int)

    both_pass = []
    both_fail = []
    only_1_pass = []  # sim1 passed (1), sim2 failed (0)
    only_2_pass = []  # sim2 passed (1), sim1 failed (0)

    for tid in all_ids:
        r1 = o1.get(tid, {}).get("reward")
        r2 = o2.get(tid, {}).get("reward")
        if r1 is None or r2 is None:
            continue
        pass1 = r1 == 1.0
        pass2 = r2 == 1.0
        rec = {
            "task_id": tid,
            "purpose": (o1.get(tid) or o2.get(tid) or {}).get("purpose", ""),
            "reason1": (o1.get(tid) or {}).get("failure_reason", ""),
            "reason2": (o2.get(tid) or {}).get("failure_reason", ""),
        }
        if pass1 and pass2:
            both_pass.append(rec)
        elif not pass1 and not pass2:
            both_fail.append(rec)
        elif pass1 and not pass2:
            only_1_pass.append(rec)
        else:
            only_2_pass.append(rec)

    name1 = path1.name[:50]
    name2 = path2.name[:50]
    print("=" * 80)
    print("SIMULATION COMPARISON")
    print("Sim1 (newer):", name1)
    print("Sim2 (older):", name2)
    print("=" * 80)
    print()
    print("OVERLAP: Both SUCCEED —", len(both_pass), "tasks")
    for r in both_pass:
        print("  Task", r["task_id"], "—", (r["purpose"] or "")[:70])
    print()
    print("OVERLAP: Both FAIL —", len(both_fail), "tasks")
    for r in both_fail:
        print("  Task", r["task_id"], "—", (r["purpose"] or "")[:70])
        if r["reason1"]:
            print("    Sim1 reason:", r["reason1"][:100])
        if r["reason2"]:
            print("    Sim2 reason:", r["reason2"][:100])
    print()
    print("DIVERGENCE: Sim1 SUCCEEDS, Sim2 FAILS —", len(only_1_pass), "tasks")
    for r in only_1_pass:
        print("  Task", r["task_id"], "—", (r["purpose"] or "")[:70])
        if r["reason2"]:
            print("    Why Sim2 failed:", r["reason2"][:120])
    print()
    print("DIVERGENCE: Sim2 SUCCEEDS, Sim1 FAILS —", len(only_2_pass), "tasks")
    for r in only_2_pass:
        print("  Task", r["task_id"], "—", (r["purpose"] or "")[:70])
        if r["reason1"]:
            print("    Why Sim1 failed:", r["reason1"][:120])
    print()
    print("SUMMARY")
    print("  Both pass:", len(both_pass), "| Both fail:", len(both_fail))
    print("  Only Sim1 passes:", len(only_1_pass), "| Only Sim2 passes:", len(only_2_pass))
    print("  Sim1 pass rate:", sum(1 for i in all_ids if (o1.get(i) or {}).get("reward") == 1.0), "/", len(o1))
    print("  Sim2 pass rate:", sum(1 for i in all_ids if (o2.get(i) or {}).get("reward") == 1.0), "/", len(o2))


if __name__ == "__main__":
    main()
