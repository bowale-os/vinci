"""
Seed Snowflake cci_edits from CMS NCCI Q1 2026 PTP edit files.

CMS gates PTP downloads behind an AMA license page — cannot be automated.

HOW TO GET THE FILES (one-time manual step):
  1. Go to https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits
  2. Click each Q1 2026 link (8 total — 4 practitioner, 4 hospital):
       Practitioner:
         medicare-ncci-2026q1-practitioner-ptp-edits-ccipra-v320r0-f1.zip
         medicare-ncci-2026q1-practitioner-ptp-edits-ccipra-v320r0-f2.zip
         medicare-ncci-2026q1-practitioner-ptp-edits-ccipra-v320r0-f3.zip
         medicare-ncci-2026q1-practitioner-ptp-edits-ccipra-v320r0-f4.zip
       Hospital Outpatient:
         medicare-ncci-2026q1-hospital-ptp-edits-ccioph-v320r0-f1.zip
         medicare-ncci-2026q1-hospital-ptp-edits-ccioph-v320r0-f2.zip
         medicare-ncci-2026q1-hospital-ptp-edits-ccioph-v320r0-f3.zip
         medicare-ncci-2026q1-hospital-ptp-edits-ccioph-v320r0-f4.zip
  3. Accept the AMA license and save each ZIP to backend/data/ncci_ptp/
  4. Run this script

File layout (tab-delimited TXT inside each ZIP):
  col 0  column_one_cpt
  col 1  column_two_cpt
  col 2  (empty)
  col 3  effective_date (YYYYMMDD)
  col 4  deletion_date  (YYYYMMDD or * = never deleted)
  col 5  modifier_indicator (0=not allowed, 1=allowed, 9=not applicable)
"""
import io
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.snowflake_client import get_connection

DATA_DIR = Path(__file__).parent.parent / "data" / "ncci_ptp"

SERVICE_MAP = {
    "ccipra": "practitioner",
    "ccioph": "outpatient",
}

BATCH = 5_000

_CPT_RE = re.compile(r'^[A-Z0-9]{5}$')


def _parse_date(s: str) -> date | None:
    s = s.strip()
    if not s or s in ("99999999", "*"):
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except Exception:
        return None


def _parse_ptp_file(content: bytes, service_type: str) -> list[tuple]:
    rows = []
    for line in content.decode("latin-1").splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        col1 = parts[0].strip().upper()
        col2 = parts[1].strip().upper()
        if not _CPT_RE.match(col1) or not _CPT_RE.match(col2):
            continue
        eff  = _parse_date(parts[3]) if len(parts) > 3 else None
        del_ = _parse_date(parts[4]) if len(parts) > 4 else None
        mod_str = parts[5].strip() if len(parts) > 5 else "0"
        mod_ind = int(mod_str) if mod_str.isdigit() else 0
        rows.append((col1, col2, mod_ind, eff, del_, service_type))
    return rows


def _batch_insert(cur, rows: list[tuple]) -> int:
    total = 0
    for i in range(0, len(rows), BATCH):
        chunk = rows[i: i + BATCH]
        placeholders = ",".join(["(%s,%s,%s,%s,%s,%s)"] * len(chunk))
        flat = [v for row in chunk for v in row]
        cur.execute(
            "INSERT INTO cci_edits "
            "(column_one_cpt,column_two_cpt,modifier_indicator,"
            "effective_date,deletion_date,service_type) "
            f"VALUES {placeholders}",
            flat,
        )
        total += len(chunk)
    return total


def seed():
    if not DATA_DIR.exists():
        print(f"  SKIP: {DATA_DIR} does not exist.")
        return

    # Prefer extracted .txt files; only fall back to .zip if no txt found
    txt_files = sorted(DATA_DIR.glob("*.txt")) + sorted(DATA_DIR.glob("*.TXT"))
    zip_files = [] if txt_files else sorted(DATA_DIR.glob("*.zip"))

    if not txt_files and not zip_files:
        print(f"  SKIP: No .txt or .zip files found in {DATA_DIR}")
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("USE DATABASE vinci_db")
    cur.execute("USE SCHEMA insurer_policies")
    cur.execute("DELETE FROM cci_edits")

    total = 0

    # Process extracted .txt files directly
    for txt_path in txt_files:
        stype = "practitioner"
        for key, label in SERVICE_MAP.items():
            if key in txt_path.name.lower():
                stype = label
                break
        print(f"  Processing {txt_path.name} ({stype}) …")
        rows = _parse_ptp_file(txt_path.read_bytes(), stype)
        n = _batch_insert(cur, rows)
        total += n
        print(f"    {n:,} rows")

    # Process any remaining ZIPs
    for zip_path in zip_files:
        stype = "practitioner"
        for key, label in SERVICE_MAP.items():
            if key in zip_path.name.lower():
                stype = label
                break
        print(f"  Processing {zip_path.name} ({stype}) …")
        with zipfile.ZipFile(zip_path) as zf:
            for fname in [n for n in zf.namelist() if n.lower().endswith(".txt")]:
                rows = _parse_ptp_file(zf.read(fname), stype)
                n = _batch_insert(cur, rows)
                total += n
                print(f"    {fname}: {n:,} rows")

    conn.commit()
    conn.close()
    print(f"  Total CCI edits seeded: {total:,} ✓")


if __name__ == "__main__":
    seed()
