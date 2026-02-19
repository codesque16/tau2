#!/usr/bin/env python3
"""
Compute cost / (input_tokens + 6*output_tokens) per agent API call for one task.

Two cost entries:
- cost: current (unchanged) full billing from the API.
- cost_cache_aware: charges only cache_creation_tokens at input price + completion_tokens
  at output price (no charge for cache read). Present only when usage has cache breakdown.

Usage: python scripts/cost_token_ratio.py <simulation.json> [task_id]
Default task_id is "0".
"""
import json
import sys
from pathlib import Path


def _weighted_tokens(u: dict) -> tuple[int, int, int, int]:
    """(prompt_tokens, completion_tokens, cached_tokens, cache_creation_tokens) -> weighted = prompt + cache_creation + 6*completion."""
    inp = u.get("prompt_tokens") or 0
    out = u.get("completion_tokens") or 0
    cached = u.get("cached_tokens") or 0  # cache read
    cache_creation = u.get("cache_creation_tokens") or 0  # cache input (written)
    # Denominator: input (prompt) + cache creation tokens + 6*output; cached_tokens are typically part of prompt_tokens
    weighted = inp + cache_creation + 6 * out
    return inp, out, cached, cache_creation, weighted


def agent_call_ratios(sim: dict) -> list[dict]:
    """Per agent (assistant) API call: cost, tokens, cache fields, weighted_tokens, ratio."""
    results = []
    for msg in sim.get("messages", []):
        if msg.get("role") != "assistant":
            continue
        c = msg.get("cost")
        u = msg.get("usage")
        if c is None or not u:
            continue
        inp, out, cached, cache_creation, weighted = _weighted_tokens(u)
        ratio = c / weighted if weighted else float("nan")
        results.append({
            "turn_idx": msg.get("turn_idx"),
            "cost": c,
            "cost_cache_aware": msg.get("cost_cache_aware"),
            "prompt_tokens": inp,
            "completion_tokens": out,
            "cached_tokens": cached,
            "cache_creation_tokens": cache_creation,
            "weighted_tokens": weighted,
            "ratio": ratio,
        })
    return results


def main() -> None:
    path = Path(sys.argv[1])
    task_id = sys.argv[2] if len(sys.argv) > 2 else "0"
    with open(path) as f:
        data = json.load(f)
    sims = data.get("simulations", [])
    sim = next((s for s in sims if s.get("task_id") == task_id), None)
    if not sim:
        print(f"Task id '{task_id}' not found. Available: {[s.get('task_id') for s in sims[:5]]}...")
        sys.exit(1)
    calls = agent_call_ratios(sim)
    print(f"Task id: {task_id} — agent API calls only\n")
    total_cost = 0.0
    total_cost_cache_aware = 0.0
    total_weighted = 0
    has_cache_aware = False
    for i, r in enumerate(calls, 1):
        total_cost += r["cost"]
        total_weighted += r["weighted_tokens"]
        cca = r.get("cost_cache_aware")
        if cca is not None:
            total_cost_cache_aware += cca
            has_cache_aware = True
        cache_part = ""
        if r.get("cached_tokens") or r.get("cache_creation_tokens"):
            cache_part = f"  cached_read={r.get('cached_tokens', 0)} cache_in={r.get('cache_creation_tokens', 0)}"
        line = (f"  Call {i} (turn {r['turn_idx']}): cost={r['cost']:.6f}  "
                f"in={r['prompt_tokens']} out={r['completion_tokens']}{cache_part}  "
                f"weighted={r['weighted_tokens']}  ratio={r['ratio']:.10f}")
        if cca is not None:
            line += f"  cost_cache_aware={cca:.6f}"
        print(line)
    if calls:
        overall = total_cost / total_weighted if total_weighted else float("nan")
        print(f"\n  Agent total: cost={total_cost:.6f}, weighted_tokens={total_weighted}, "
              f"ratio (cost/weighted) = {overall:.10f}")
        if has_cache_aware:
            print(f"  Agent total (cache-aware): cost_cache_aware={total_cost_cache_aware:.6f}")
        print(f"  Per-call ratio: min={min(r['ratio'] for r in calls):.10f}, "
              f"max={max(r['ratio'] for r in calls):.10f}, "
              f"mean={sum(r['ratio'] for r in calls)/len(calls):.10f}")
    else:
        print("  No agent messages with cost and usage found.")


if __name__ == "__main__":
    main()
