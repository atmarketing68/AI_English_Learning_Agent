"""
AGEN — Pre-generate curriculum lesson content (Content Factory CLI).

Generates + caches AI lesson content for curriculum nodes so learners are served
stable, reviewed, quota-free lessons instead of triggering live LLM calls.

Usage (run from the agen-backend directory, with the venv active):

    # Generate ALL generatable nodes for a level, auto-approve, skip existing:
    python scripts/pregenerate_content.py --level A1 --auto-approve

    # Generate several levels:
    python scripts/pregenerate_content.py --level A1 --level A2 --auto-approve

    # Generate a single node:
    python scripts/pregenerate_content.py --code A2-U01-L01 --auto-approve

    # Regenerate even if cached (overwrite):
    python scripts/pregenerate_content.py --level A1 --force --auto-approve

    # Limit how many nodes to generate (useful to conserve LLM quota):
    python scripts/pregenerate_content.py --level A1 --limit 5 --auto-approve

Notes:
  - Each node = one LLM call. Mind your provider's daily quota.
  - Without --auto-approve, content is saved as 'draft' for later review/approval
    (via the admin API or admin UI). Learners are only served APPROVED content.
"""
import argparse
import os
import sys

# Force UTF-8 stdout/stderr so Vietnamese messages (and any Unicode in errors)
# print correctly on Windows consoles (default cp1252 would crash).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from dotenv import load_dotenv

# Load .env + make the app importable when run as a standalone script.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal  # noqa: E402
from app.services.curriculum_seed import seed_curriculum  # noqa: E402
from app.services.curriculum_content_service import (  # noqa: E402
    batch_generate_level,
    generate_and_cache,
    ContentGenerationError,
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pre-generate curriculum lesson content.")
    p.add_argument("--level", action="append", default=[], help="Level to generate (repeatable), e.g. A1")
    p.add_argument("--code", action="append", default=[], help="Single curriculum code (repeatable), e.g. A2-U01-L01")
    p.add_argument("--force", action="store_true", help="Regenerate even if cached content exists")
    p.add_argument("--auto-approve", action="store_true", help="Mark generated content as approved immediately")
    p.add_argument("--limit", type=int, default=None, help="Max nodes to generate per level")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.level and not args.code:
        print("Nothing to do. Pass --level and/or --code. See --help.")
        return 1

    db = SessionLocal()
    try:
        # Ensure the curriculum map exists (idempotent) before generating content.
        seed_curriculum(db)

        total_generated = total_failed = 0

        for code in args.code:
            print(f"-> Generating node {code} ...", flush=True)
            try:
                row = generate_and_cache(db, code, force=args.force, auto_approve=args.auto_approve)
                db.commit()
                total_generated += 1
                flag = " [FLAGGED]" if row.eval_flagged else ""
                print(f"  [OK] {code}: status={row.status} score={row.eval_score}{flag}")
            except ContentGenerationError as exc:
                db.rollback()
                total_failed += 1
                print(f"  [FAIL] {code}: {exc}")

        for level in args.level:
            print(f"\n-> Generating level {level} (auto_approve={args.auto_approve}, force={args.force}) ...", flush=True)
            summary = batch_generate_level(
                db, level, force=args.force, auto_approve=args.auto_approve, limit=args.limit,
            )
            total_generated += summary["generated"]
            total_failed += summary["failed"]
            print(
                f"  level={summary['level']} generated={summary['generated']} "
                f"skipped={summary['skipped']} failed={summary['failed']}"
            )
            for err in summary["errors"]:
                print(f"    [FAIL] {err['code']}: {err['error']}")

        print(f"\nDone. generated={total_generated} failed={total_failed}")
        return 0 if total_failed == 0 else 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
