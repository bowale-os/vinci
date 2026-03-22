"""
Seed Snowflake fda_products from openFDA bulk download endpoints.

Fetches:
  - Drug product labels (indications, warnings, approval info)
  - 510(k) device clearances
  - PMA device approvals

openFDA bulk download index: https://api.fda.gov/download.json
"""
import asyncio
import gzip
import io
import json
import sys
import zipfile
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.snowflake_client import get_connection

OPENFDA_DOWNLOAD_INDEX = "https://api.fda.gov/download.json"
BATCH = 500

INDICATION_KEYWORDS = [
    "treatment", "indicated for", "indicated in", "approved for",
    "therapy", "chronic", "acute", "syndrome", "disease", "disorder",
]


def _safe_str(val) -> str:
    if isinstance(val, list):
        return " ".join(str(v) for v in val)
    return str(val) if val else ""


def _decompress(raw: bytes) -> bytes:
    """Handle both gzip (.json.gz) and zip (.zip) openFDA part files."""
    if raw[:2] == b'PK':
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            return zf.read(zf.namelist()[0])
    return gzip.decompress(raw)


def _extract_drug_row(rec: dict) -> dict | None:
    openfda = rec.get("openfda", {})
    brand = _safe_str(openfda.get("brand_name", [""])[:1])
    generic = _safe_str(openfda.get("generic_name", [""])[:1])
    if not brand and not generic:
        return None
    indications = _safe_str(rec.get("indications_and_usage", ""))
    if not indications:
        return None
    app_num = _safe_str(openfda.get("application_number", [""])[:1])
    return {
        "product_id": f"drug_{app_num}_{brand[:30]}".lower().replace(" ", "_")[:100],
        "product_type": "drug",
        "brand_name": brand[:300],
        "generic_name": generic[:300],
        "ndc_codes": openfda.get("package_ndc", [])[:10],
        "indications_text": indications[:5000],
        "contraindications_text": _safe_str(rec.get("contraindications", ""))[:3000],
        "black_box_warnings": _safe_str(rec.get("boxed_warning", ""))[:2000],
        "fda_approval_date": None,
        "approval_type": app_num[:5] or "NDA",
        "application_number": app_num[:50],
        "sponsor_name": _safe_str(openfda.get("manufacturer_name", [""])[:1])[:300],
    }


def _extract_device_row(rec: dict, approval_type: str) -> dict | None:
    device_name = rec.get("device_name", "") or rec.get("trade_name", "")
    if not device_name:
        return None
    app_num = rec.get("k_number") or rec.get("pma_number") or ""
    return {
        "product_id": f"device_{approval_type}_{app_num}".lower().replace(" ", "_")[:100],
        "product_type": "device",
        "brand_name": str(device_name)[:300],
        "generic_name": str(rec.get("generic_name", "") or rec.get("device_name", ""))[:300],
        "ndc_codes": [],
        "indications_text": str(rec.get("statement_or_summary", "") or "")[:5000],
        "contraindications_text": "",
        "black_box_warnings": "",
        "fda_approval_date": rec.get("decision_date") or rec.get("date_received"),
        "approval_type": approval_type,
        "application_number": str(app_num)[:50],
        "sponsor_name": str(rec.get("applicant", "") or rec.get("company", ""))[:300],
    }


def _upsert_batch(cur, rows: list[dict]):
    for row in rows:
        try:
            cur.execute("""
                MERGE INTO fda_products AS tgt
                USING (SELECT %s AS product_id) AS src ON tgt.product_id = src.product_id
                WHEN NOT MATCHED THEN INSERT (
                    product_id, product_type, brand_name, generic_name, ndc_codes,
                    indications_text, contraindications_text, black_box_warnings,
                    fda_approval_date, approval_type, application_number, sponsor_name
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                row["product_id"], row["product_id"],
                row["product_type"], row["brand_name"], row["generic_name"],
                row["ndc_codes"], row["indications_text"],
                row["contraindications_text"], row["black_box_warnings"],
                row["fda_approval_date"], row["approval_type"],
                row["application_number"], row["sponsor_name"],
            ))
        except Exception:
            pass


async def _fetch_parts(client: httpx.AsyncClient, dataset_key: str, part_key: str) -> list[dict]:
    """Download first 3 part files from openFDA bulk index."""
    index_resp = await client.get(OPENFDA_DOWNLOAD_INDEX, timeout=30)
    index = index_resp.json()

    parts = index.get("results", {}).get(dataset_key, {}).get(part_key, {}).get("partitions", [])
    if not parts:
        print(f"    No partitions found for {dataset_key}/{part_key}")
        return []

    records = []
    for part in parts[:3]:
        url = part.get("file")
        if not url:
            continue
        try:
            resp = await client.get(url, timeout=120)
            resp.raise_for_status()
            content = _decompress(resp.content)
            data = json.loads(content)
            records.extend(data.get("results", []))
        except Exception as e:
            print(f"    Part fetch error ({url[-40:]}): {e}")

    return records


async def download_and_seed():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("USE DATABASE vinci_db")
    cur.execute("USE SCHEMA insurer_policies")

    total = 0
    async with httpx.AsyncClient() as client:
        print("Fetching openFDA drug labels …")
        drug_records = await _fetch_parts(client, "drug", "label")
        drug_rows = [r for rec in drug_records if (r := _extract_drug_row(rec))]
        _upsert_batch(cur, drug_rows)
        total += len(drug_rows)
        print(f"  Drug rows: {len(drug_rows):,}")

        print("Fetching openFDA 510k devices …")
        dev_510k = await _fetch_parts(client, "device", "510k")
        dev_rows = [r for rec in dev_510k if (r := _extract_device_row(rec, "510k"))]
        _upsert_batch(cur, dev_rows)
        total += len(dev_rows)
        print(f"  510k rows: {len(dev_rows):,}")

        print("Fetching openFDA PMA devices …")
        dev_pma = await _fetch_parts(client, "device", "pma")
        pma_rows = [r for rec in dev_pma if (r := _extract_device_row(rec, "PMA"))]
        _upsert_batch(cur, pma_rows)
        total += len(pma_rows)
        print(f"  PMA rows: {len(pma_rows):,}")

    conn.commit()
    conn.close()
    print(f"  Total FDA products seeded: {total:,} ✓")


if __name__ == "__main__":
    asyncio.run(download_and_seed())
