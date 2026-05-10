"""Standalone test entry point for the L1→L2 compression subgraph.

Usage:
    # Interactive mode (prompts for Q and A)
    PYTHONPATH=src python scripts/test_compression.py

    # Direct args
    PYTHONPATH=src python scripts/test_compression.py \
        --q "什麼是 LangGraph？" \
        --a "LangGraph 是一個基於有向圖的框架..."

    # Verbose: show L1 annotated segments (long path only)
    PYTHONPATH=src python scripts/test_compression.py --verbose

Output shows:
    - route          : short | long
    - L1 annotated   : segment list with KEEP/COMPRESS/DROP labels (long path only)
    - sum            : final compression result
    - fallback used  : whether sum came from fallback (q[:100]) or real LLM output
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: load .env before importing agent modules
# ---------------------------------------------------------------------------

_repo_root = Path(__file__).parent.parent
_env_path = _repo_root / ".env"
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())

sys.path.insert(0, str(_repo_root / "src"))

# ---------------------------------------------------------------------------
# Imports (after path setup)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(name)s  %(message)s",
)
# Silence noisy third-party loggers
for _noisy in ("httpx", "httpcore", "urllib3"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Patched run: captures intermediate state for display
# ---------------------------------------------------------------------------


async def _run_verbose(q: str, a: str) -> None:
    """Run compression and print detailed intermediate state."""
    import time

    from agent.compression.graph import (
        CompressionState,
        l1_annotate,
        l2_compress,
        router,
    )
    from agent.compression.prompts import (
        L1_SYSTEM,
        L1_USER_TEMPLATE,
        L2_ANNOTATED_SYSTEM,
        L2_ANNOTATED_USER_TEMPLATE,
        L2_SHORT_SYSTEM,
        L2_SHORT_USER_TEMPLATE,
        SHORT_THRESHOLD,
    )

    state: CompressionState = {
        "node_id": "test",
        "q": q,
        "a": a,
        "route": "",
        "annotated": "",
        "sum": "",
    }

    t_total = time.perf_counter()

    # Step 1: router
    state.update(router(state))  # type: ignore[arg-type]
    print(f"\n{'─'*60}")
    print(f"  route      : {state['route']}  (threshold={SHORT_THRESHOLD})")
    print(f"  answer len : {len(a)} chars")

    # Step 2: L1 (long path only)
    if state["route"] == "long":
        _paragraphs = [p.strip() for p in state["a"][:4000].split("\n\n") if p.strip()] or [state["a"][:4000]]
        _seg_numbered = "\n".join(f"[{i}] {p}" for i, p in enumerate(_paragraphs))
        rendered = L1_USER_TEMPLATE.format(q=state["q"], segments_numbered=_seg_numbered)
        print(f"\n{'─'*60}")
        print(f"  L1 system  :\n    {L1_SYSTEM.replace(chr(10), chr(10)+'    ')}")
        print(f"\n  L1 user    :\n    {rendered[:600].replace(chr(10), chr(10)+'    ')}")
        print(f"\n  L1 annotate  (calling model...)")
        t0 = time.perf_counter()
        state.update(await l1_annotate(state))  # type: ignore[arg-type]
        dt = time.perf_counter() - t0
        annotated = state["annotated"]
        if annotated:
            print(f"  ({dt:.2f}s)\n")
            for line in annotated.splitlines():
                print(f"    {line}")
        else:
            print(f"  ({dt:.2f}s)  (empty — fallback to raw answer)")

    # Step 3: L2
    use_annotated = state["route"] == "long" and bool(state["annotated"])
    if use_annotated:
        rendered = L2_ANNOTATED_USER_TEMPLATE.format(q=state["q"], annotated=state["annotated"])
        sys_msg = L2_ANNOTATED_SYSTEM
    else:
        rendered = L2_SHORT_USER_TEMPLATE.format(q=state["q"], a=state["a"][:3000])
        sys_msg = L2_SHORT_SYSTEM
    print(f"\n{'─'*60}")
    print(f"  L2 system  :\n    {sys_msg.replace(chr(10), chr(10)+'    ')}")
    print(f"\n  L2 user    :\n    {rendered[:600].replace(chr(10), chr(10)+'    ')}")
    print(f"\n  L2 compress  (calling model...)")
    t0 = time.perf_counter()
    state.update(await l2_compress(state))  # type: ignore[arg-type]
    dt = time.perf_counter() - t0

    sum_text: str = state["sum"]
    fallback_used = False
    if not sum_text:
        sum_text = q[:100] + ("..." if len(q) > 100 else "")
        fallback_used = True

    total = time.perf_counter() - t_total
    print(f"\n{'='*60}")
    print(f"  sum          : {sum_text}")
    print(f"  L2 time      : {dt:.2f}s")
    print(f"  total time   : {total:.2f}s")
    if fallback_used:
        print("  ⚠  fallback used (L2 returned empty — Ollama down?)")
    print(f"{'='*60}\n")


async def _run_simple(q: str, a: str) -> None:
    """Run compression via the public entry point."""
    import time

    from agent.compression.graph import run_compression
    from agent.compression.prompts import SHORT_THRESHOLD

    route = "short" if len(a) < SHORT_THRESHOLD else "long"
    print(f"\n{'─'*60}")
    print(f"  route      : {route}  (threshold={SHORT_THRESHOLD})")
    print(f"  answer len : {len(a)} chars")
    print("  running compression...")
    t0 = time.perf_counter()

    sum_text = await run_compression(q, a, node_id="test")
    elapsed = time.perf_counter() - t0
    fallback_used = sum_text.rstrip(".") == q[:100].rstrip(".")

    print(f"\n{'='*60}")
    print(f"  sum        : {sum_text}")
    print(f"  total time : {elapsed:.2f}s")
    if fallback_used:
        print("  ⚠  fallback used (Ollama down?)")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Test the L1→L2 compression subgraph in isolation."
    )
    p.add_argument("--q", help="Question string")
    p.add_argument("--a", help="Answer string")
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show L1 segments and step-by-step output",
    )
    return p.parse_args()


async def main() -> None:
    args = _parse_args()

    # Interpret escape sequences so --a "line1\nline2" becomes actual newlines
    q = args.q.encode("raw_unicode_escape").decode("unicode_escape") if args.q else None
    a = args.a.encode("raw_unicode_escape").decode("unicode_escape") if args.a else None

    if not q:
        print("── Compression subgraph test ──")
        q = input("Q (question): ").strip()
    if not a:
        print("A (answer) — enter text, finish with a blank line:")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        a = "\n".join(lines).strip()

    if not q or not a:
        print("Error: both Q and A are required.")
        sys.exit(1)

    if args.verbose:
        await _run_verbose(q, a)
    else:
        await _run_simple(q, a)


if __name__ == "__main__":
    asyncio.run(main())
