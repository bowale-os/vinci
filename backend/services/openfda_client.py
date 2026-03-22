"""
openFDA live query client.

Endpoints used:
  /drug/label.json        — indications, warnings, approval info
  /device/510k.json       — 510(k) clearances
  /device/pma.json        — PMA approvals
"""
import httpx

BASE = "https://api.fda.gov"


async def search_drug(name: str) -> list[dict]:
    """
    Search drug labels by brand name or generic name.
    Returns list of dicts with keys: brand, generic, indications, approval_type, approval_date, warnings.
    """
    # Try Snowflake cache first
    from services.snowflake_client import query as sf_query
    cached = sf_query(
        "SELECT brand_name, generic_name, indications_text, approval_type, "
        "fda_approval_date, black_box_warnings FROM fda_products "
        "WHERE product_type = 'drug' AND (LOWER(brand_name) LIKE %s OR LOWER(generic_name) LIKE %s) "
        "LIMIT 5",
        (f"%{name.lower()}%", f"%{name.lower()}%"),
    )
    if cached:
        return [
            {
                "brand": r["BRAND_NAME"],
                "generic": r["GENERIC_NAME"],
                "indications": r["INDICATIONS_TEXT"],
                "approval_type": r["APPROVAL_TYPE"],
                "approval_date": str(r["FDA_APPROVAL_DATE"] or ""),
                "warnings": r["BLACK_BOX_WARNINGS"],
            }
            for r in cached
        ]

    # Live API fallback
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{BASE}/drug/label.json", params={
            "search": f'openfda.brand_name:"{name}" openfda.generic_name:"{name}"',
            "limit": 5,
        })
        if resp.status_code != 200:
            return []
        results = resp.json().get("results", [])

    out = []
    for r in results:
        openfda = r.get("openfda", {})
        out.append({
            "brand": " / ".join(openfda.get("brand_name", [])[:2]),
            "generic": " / ".join(openfda.get("generic_name", [])[:2]),
            "indications": " ".join(r.get("indications_and_usage", []))[:3000],
            "approval_type": " / ".join(openfda.get("application_number", [])[:1])[:5] or "NDA",
            "approval_date": "",
            "warnings": " ".join(r.get("boxed_warning", []))[:1000],
        })
    return out


async def search_device(name: str) -> list[dict]:
    """
    Search 510(k) and PMA device clearances by device name.
    Returns list of dicts.
    """
    from services.snowflake_client import query as sf_query
    cached = sf_query(
        "SELECT brand_name, generic_name, indications_text, approval_type, "
        "fda_approval_date, application_number FROM fda_products "
        "WHERE product_type = 'device' AND LOWER(brand_name) LIKE %s LIMIT 5",
        (f"%{name.lower()}%",),
    )
    if cached:
        return [
            {
                "device_name": r["BRAND_NAME"],
                "device_type": r["GENERIC_NAME"],
                "indications": r["INDICATIONS_TEXT"],
                "clearance_type": r["APPROVAL_TYPE"],
                "decision_date": str(r["FDA_APPROVAL_DATE"] or ""),
                "application_number": r["APPLICATION_NUMBER"],
            }
            for r in cached
        ]

    out = []
    async with httpx.AsyncClient(timeout=20) as client:
        for endpoint, ctype in [("/device/510k.json", "510(k)"), ("/device/pma.json", "PMA")]:
            resp = await client.get(f"{BASE}{endpoint}", params={
                "search": f'device_name:"{name}"', "limit": 3,
            })
            if resp.status_code != 200:
                continue
            for r in resp.json().get("results", []):
                out.append({
                    "device_name": r.get("device_name", r.get("trade_name", "")),
                    "device_type": r.get("device_name", ""),
                    "indications": r.get("statement_or_summary", "")[:2000],
                    "clearance_type": ctype,
                    "decision_date": r.get("decision_date", r.get("date_received", "")),
                    "application_number": r.get("k_number", r.get("pma_number", "")),
                })
    return out
