"""
Orchestrator — run all seeders in the correct order.
Usage:  cd backend && python seeders/run_all.py

Order:
  1. Apply DDL (create tables if not exist)
  2. seed_states    — fast, no network
  3. seed_ncds      — small (~180 rows)
  4. seed_lcds      — medium (~2000 rows)
  5. seed_cci       — large (~1M rows, batched)
  6. seed_mue       — medium (~10k rows)
  7. seed_fda       — large (filtered subset)
  8. seed_vectors   — embed text cols → MongoDB
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.snowflake_client import get_connection


def apply_ddl():
    print("\n── Applying Snowflake DDL ──────────────────────────────────────")
    ddl_path = Path(__file__).parent.parent / "data" / "snowflake_ddl.sql"
    sql = ddl_path.read_text()
    conn = get_connection()
    cur = conn.cursor()
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            try:
                cur.execute(stmt)
            except Exception as e:
                print(f"  DDL warning: {e}")
    conn.commit()
    conn.close()
    print("  DDL applied ✓")


def run_seeder(name: str, fn):
    print(f"\n── {name} ────────────────────────────────────────────────────")
    t0 = time.time()
    try:
        if asyncio.iscoroutinefunction(fn):
            asyncio.run(fn())
        else:
            fn()
        print(f"  Done in {time.time()-t0:.1f}s")
    except Exception as e:
        print(f"  ERROR in {name}: {e}")


if __name__ == "__main__":
    from seeders import seed_states, seed_lcd_ncd, seed_cci, seed_mue, seed_fda, seed_vectors, seed_cpbs, seed_guidelines

    apply_ddl()
    run_seeder("States",              seed_states.seed)
    run_seeder("LCDs + NCDs",         seed_lcd_ncd.seed)
    run_seeder("CPBs",                seed_cpbs.seed)
    run_seeder("Clinical Guidelines", seed_guidelines.seed)
    run_seeder("CCI Edits",           seed_cci.seed)
    run_seeder("MUE Edits",           seed_mue.seed)
    run_seeder("FDA Products",        seed_fda.download_and_seed)
    run_seeder("Vectors → MongoDB",   seed_vectors.seed_all)

    print("\n═══════════════════════════════════════")
    print("  All seeders complete. Vinci DB ready.")
    print("═══════════════════════════════════════\n")
