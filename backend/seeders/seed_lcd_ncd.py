"""
seed_lcd_ncd.py — Ingest LCD and NCD CSVs into Snowflake.

Column mappings verified against actual CSV headers on 2026-03-22.

LCD source files:
  lcd.csv                    — lcd_id, title, status, orig_det_eff_date, indication, …
  lcd_x_hcpc_code.csv        — lcd_id, hcpc_code_id
  lcd_x_contractor.csv       — lcd_id, contractor_id
  contractor_jurisdiction.csv — contractor_id, state_id
  state_lookup.csv           — state_id, state_abbrev

NCD source files:
  ncd_trkg.csv               — NCD_id, NCD_mnl_sect_title, NCD_mnl_sect, indctn_lmtn, itm_srvc_desc, …
  ncd_trkg_bnft_xref.csv     — NCD_id, bnft_ctgry_cd
  ncd_bnft_ctgry_ref.csv     — bnft_ctgry_cd, bnft_ctgry_desc
"""
import csv
import re
import sys
from pathlib import Path

# Windows: sys.maxsize overflows C long — use 2**31-1
csv.field_size_limit(2 ** 31 - 1)

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.snowflake_client import get_connection

DATA  = Path(__file__).parent.parent / "data"
BATCH = 500


def clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return re.sub(r"\s+", " ", text).strip()


def parse_date(val: str) -> str | None:
    """Strip time component from 'YYYY-MM-DD HH:MM:SS' → 'YYYY-MM-DD'."""
    if not val or not val.strip():
        return None
    return val.strip()[:10] or None


def read_csv(filename: str) -> list[dict]:
    path = DATA / filename
    if not path.exists():
        print(f"  WARNING: {filename} not found, skipping")
        return []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def batch_insert(cur, table: str, columns: list[str], rows: list[tuple]) -> int:
    if not rows:
        return 0
    ph      = ",".join(["%s"] * len(columns))
    col_str = ",".join(columns)
    total   = 0
    for i in range(0, len(rows), BATCH):
        chunk      = rows[i: i + BATCH]
        values_sql = ",".join([f"({ph})"] * len(chunk))
        flat       = [v for row in chunk for v in row]
        cur.execute(f"INSERT INTO {table} ({col_str}) VALUES {values_sql}", flat)
        total += len(chunk)
    return total


def seed_lcds(cur) -> int:
    print("Seeding lcds …")
    cur.execute("DELETE FROM lcds")

    # state_id (numeric) → 2-letter abbreviation
    state_map: dict[str, str] = {
        r["state_id"]: r["state_abbrev"]
        for r in read_csv("state_lookup.csv")
        if r.get("state_id") and r.get("state_abbrev")
    }

    # contractor_id+type → list of state abbreviations
    contractor_states: dict[str, list[str]] = {}
    for row in read_csv("contractor_jurisdiction.csv"):
        key    = row.get("contractor_id", "").strip()
        sid    = row.get("state_id", "").strip()
        abbrev = state_map.get(sid, "")
        if key and abbrev:
            contractor_states.setdefault(key, []).append(abbrev)

    # lcd_id → set of state abbreviations
    lcd_states_map: dict[str, set[str]] = {}
    for row in read_csv("lcd_x_contractor.csv"):
        lcd_id = row.get("lcd_id", "").strip()
        cid    = row.get("contractor_id", "").strip()
        if lcd_id and cid:
            lcd_states_map.setdefault(lcd_id, set()).update(
                contractor_states.get(cid, [])
            )

    # lcd_id → list of CPT/HCPCS codes
    lcd_codes_map: dict[str, list[str]] = {}
    for row in read_csv("lcd_x_hcpc_code.csv"):
        lcd_id = row.get("lcd_id", "").strip()
        code   = row.get("hcpc_code_id", "").strip()
        if lcd_id and code:
            lcd_codes_map.setdefault(lcd_id, []).append(code)

    all_lcd_rows = read_csv("lcd.csv")
    print(f"  Found {len(all_lcd_rows):,} LCD rows (before dedup)")

    # lcd.csv has one row per (lcd_id, lcd_version). Keep only the latest version.
    latest: dict[str, dict] = {}
    for r in all_lcd_rows:
        lid = r.get("lcd_id", "").strip()
        if not lid:
            continue
        ver = int(r.get("lcd_version", "0") or 0)
        if lid not in latest or ver > int(latest[lid].get("lcd_version", "0") or 0):
            latest[lid] = r
    lcd_rows = list(latest.values())
    print(f"  {len(lcd_rows):,} unique LCDs after dedup")

    rows = []
    for r in lcd_rows:
        lcd_id = r.get("lcd_id", "").strip()
        if not lcd_id:
            continue

        indication = clean_html(r.get("indication", ""))
        full_text  = indication  # main embeddable text

        if not full_text.strip():
            continue

        state_codes = ",".join(sorted(lcd_states_map.get(lcd_id, set())))
        cpt_codes   = ",".join(lcd_codes_map.get(lcd_id, [])[:200])

        rows.append((
            lcd_id,
            r.get("title", "").strip()[:500],
            r.get("status", "A").strip(),
            parse_date(r.get("orig_det_eff_date", "")),
            parse_date(r.get("rev_eff_date", "")),
            parse_date(r.get("date_retired", "")),
            full_text[:32000],
            state_codes[:500],
            cpt_codes[:5000],
        ))

    n = batch_insert(cur, "lcds", [
        "lcd_id", "lcd_name", "status",
        "original_effective_dt", "revision_effective_dt", "retirement_dt",
        "full_text", "state_codes", "cpt_codes",
    ], rows)
    print(f"  Inserted {n:,} LCD records ✓")
    return n


def seed_ncds(cur) -> int:
    print("Seeding ncds …")
    cur.execute("DELETE FROM ncds")

    # benefit category code → description
    benefit_ref: dict[str, str] = {
        r.get("bnft_ctgry_cd", ""): r.get("bnft_ctgry_desc", "")
        for r in read_csv("ncd_bnft_ctgry_ref.csv")
    }
    # NCD_id → list of benefit category descriptions
    ncd_benefits: dict[str, list[str]] = {}
    for row in read_csv("ncd_trkg_bnft_xref.csv"):
        ncd_id  = row.get("NCD_id", "").strip()
        cat_cd  = row.get("bnft_ctgry_cd", "").strip()
        if ncd_id and cat_cd:
            ncd_benefits.setdefault(ncd_id, []).append(
                benefit_ref.get(cat_cd, cat_cd)
            )

    ncd_rows = read_csv("ncd_trkg.csv")
    print(f"  Found {len(ncd_rows):,} NCD records")

    rows = []
    for r in ncd_rows:
        ncd_id = r.get("NCD_id", "").strip()
        if not ncd_id:
            continue

        title         = r.get("NCD_mnl_sect_title", "").strip()
        item_desc     = clean_html(r.get("itm_srvc_desc", ""))
        indications   = clean_html(r.get("indctn_lmtn", ""))
        full_text     = f"{title}. {item_desc} {indications}".strip()

        if not full_text.strip():
            continue

        benefits = ",".join(ncd_benefits.get(ncd_id, []))

        rows.append((
            ncd_id,
            title[:500],
            r.get("NCD_mnl_sect", "").strip(),
            parse_date(r.get("NCD_efctv_dt", "")),
            parse_date(r.get("NCD_trmntn_dt", "")),
            full_text[:32000],
            benefits[:500],
        ))

    n = batch_insert(cur, "ncds", [
        "ncd_id", "ncd_title", "manual_section",
        "effective_dt", "end_dt",
        "full_text", "benefit_categories",
    ], rows)
    print(f"  Inserted {n:,} NCD records ✓")
    return n


def seed():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("USE DATABASE vinci_db")
    cur.execute("USE SCHEMA insurer_policies")

    cur.execute("""
        CREATE OR REPLACE TABLE lcds (
            lcd_id                VARCHAR(20)   PRIMARY KEY,
            lcd_name              VARCHAR(500),
            status                VARCHAR(10),
            original_effective_dt DATE,
            revision_effective_dt DATE,
            retirement_dt         DATE,
            full_text             VARCHAR(32000),
            state_codes           VARCHAR(500),
            cpt_codes             VARCHAR(5000),
            last_updated          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """)
    cur.execute("""
        CREATE OR REPLACE TABLE ncds (
            ncd_id              VARCHAR(20)   PRIMARY KEY,
            ncd_title           VARCHAR(500),
            manual_section      VARCHAR(50),
            effective_dt        DATE,
            end_dt              DATE,
            full_text           VARCHAR(32000),
            benefit_categories  VARCHAR(500),
            last_updated        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """)

    seed_lcds(cur)
    seed_ncds(cur)

    conn.commit()
    conn.close()
    print("\nSnowflake LCD/NCD ingestion complete ✓")


if __name__ == "__main__":
    seed()
