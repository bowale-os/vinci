"""
Seed Snowflake lcds table from CMS Medicare Coverage Database.

Automatic:  downloads from CMS if network allows.
Manual fallback: drop the ZIP at  backend/data/lcd-flat-file.zip
  then re-run — the seeder will use the local file instead.

CMS download page:
  https://www.cms.gov/medicare-coverage-database/downloads/downloads.aspx
"""
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.snowflake_client import get_connection

LCD_CSV_URL = "https://www.cms.gov/medicare-coverage-database/downloads/lcd-flat-file.zip"
LOCAL_ZIP   = Path(__file__).parent.parent / "data" / "current_lcd.zip"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/zip,application/octet-stream,*/*",
}


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _parse_array_field(raw: str) -> list[str]:
    if not raw:
        return []
    sep = "|" if "|" in raw else ","
    return [c.strip() for c in raw.split(sep) if c.strip()]


def _get_zip_bytes() -> bytes:
    """Return ZIP bytes from local file if present, otherwise download."""
    if LOCAL_ZIP.exists():
        print(f"  Using local file: {LOCAL_ZIP}")
        return LOCAL_ZIP.read_bytes()

    print("  Downloading from CMS …")
    resp = httpx.get(LCD_CSV_URL, headers=_HEADERS, follow_redirects=True, timeout=120)
    resp.raise_for_status()
    if resp.content[:2] != b'PK':
        raise ValueError(
            f"CMS returned HTML instead of a ZIP — log in at cms.gov, download "
            f"lcd-flat-file.zip, and place it at backend/data/lcd-flat-file.zip\n"
            f"First bytes: {resp.content[:120]}"
        )
    return resp.content


def download_and_seed():
    print("LCD seeder starting …")
    zip_bytes = _get_zip_bytes()

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_name = next((n for n in zf.namelist() if n.lower().endswith(".csv")), None)
        if not csv_name:
            raise ValueError(f"No CSV found in ZIP. Contents: {zf.namelist()}")
        csv_bytes = zf.read(csv_name)

    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))
    rows = list(reader)
    print(f"  Parsed {len(rows):,} LCD rows from '{csv_name}'")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("USE DATABASE vinci_db")
    cur.execute("USE SCHEMA insurer_policies")

    inserted = skipped = 0
    for row in rows:
        lcd_id = row.get("LCD_ID", "").strip()
        if not lcd_id:
            skipped += 1
            continue
        cur.execute("""
            MERGE INTO lcds AS tgt
            USING (SELECT %s AS lcd_id) AS src ON tgt.lcd_id = src.lcd_id
            WHEN NOT MATCHED THEN INSERT (
                lcd_id, title, contractor, mac_jurisdiction, states,
                effective_date, status, indications_text, covered_icd10s,
                covered_cpts, noncovered_text, source_url
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            lcd_id, lcd_id,
            _clean(row.get("LCD_TITLE")),
            _clean(row.get("CONTRACTOR_NAME")),
            _clean(row.get("JURISDICTION")),
            _parse_array_field(row.get("STATES", "")),
            row.get("EFFECTIVE_DATE") or None,
            _clean(row.get("STATUS", "Active")),
            _clean(row.get("INDICATIONS_LIMITATIONS", "")),
            _parse_array_field(row.get("ICD10_CODES", "")),
            _parse_array_field(row.get("CPT_CODES", "")),
            _clean(row.get("NONCOVERED", "")),
            f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid={lcd_id}",
        ))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"  Seeded {inserted:,} LCDs ({skipped} skipped) ✓")


if __name__ == "__main__":
    download_and_seed()
