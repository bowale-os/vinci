"""
Unified coverage search: MongoDB semantic retrieval + Snowflake enrichment.

Used by the appeal agent to find relevant LCD/NCD/CPB policies for a denial.

Usage:
    from services.coverage_search import search_coverage

    results = search_coverage(
        query_text="chronic migraine CGRP inhibitor not medically necessary",
        state_code="TN",
        cpt_codes=["G0283", "99213"],
        top_k=5,
    )
    for r in results:
        print(r["source_name"], r["score"])
        print(r["chunk_text"][:300])
        print(r["snowflake_record"])   # full structured row from Snowflake
"""
from __future__ import annotations

from services.snowflake_client import query as sf_query
from services.vector_client import query as vec_query

VECTOR_CANDIDATES = 20
DEFAULT_TOP_K     = 5


def _structured_lookup(source_ids: list[str], source_type: str) -> dict[str, dict]:
    """Fetch full Snowflake rows for a list of IDs."""
    if not source_ids:
        return {}

    if source_type == "lcd":
        table, id_col = "lcds", "lcd_id"
    elif source_type == "ncd":
        table, id_col = "ncds", "ncd_id"
    elif source_type == "cpb":
        table, id_col = "cpbs", "cpb_number"
    else:
        return {}

    placeholders = ",".join([f"'{sid}'" for sid in source_ids])
    rows = sf_query(f"SELECT * FROM {table} WHERE {id_col} IN ({placeholders})")
    return {str(row.get(id_col) or row.get(id_col.upper(), "")): row for row in rows}


def search_coverage(
    query_text: str,
    state_code: str | None = None,
    cpt_codes: list[str] | None = None,
    namespaces: list[str] | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """
    Semantic search across coverage namespaces, enriched with Snowflake data.

    Args:
        query_text : free-text description of the denial / clinical scenario
        state_code : 2-letter state code — filters LCDs to patient's state
        cpt_codes  : CPT codes from the denial — pre-filters vector search
        namespaces : which namespaces to search (default: lcds, ncds, cpbs)
        top_k      : number of deduplicated results to return

    Returns:
        List of dicts with keys:
          source_type, source_id, source_name, state_codes, cpt_codes,
          chunk_text, score, snowflake_record
    """
    namespaces = namespaces or ["lcds", "ncds", "cpbs"]
    cpt_codes  = cpt_codes or []

    raw_results: list[dict] = []

    for ns in namespaces:
        # LCDs are state-specific; NCDs/CPBs are national
        sc = state_code if ns == "lcds" else None
        cc = cpt_codes  if ns in ("lcds", "cpbs") else []

        hits = vec_query(
            namespace=ns,
            query_text=query_text,
            top_k=VECTOR_CANDIDATES,
            state_code=sc,
            cpt_codes=cc or None,
        )
        raw_results.extend(hits)

    if not raw_results:
        return []

    # Deduplicate by source_id — keep highest-scoring chunk per document
    seen:   dict[str, dict] = {}
    for r in sorted(raw_results, key=lambda x: x.get("score", 0), reverse=True):
        sid = r.get("source_id") or r.get("id", "")
        if sid not in seen:
            seen[sid] = r

    top_hits = list(seen.values())[:top_k * 2]

    # Group by source type for batched Snowflake lookup
    by_type: dict[str, list[str]] = {}
    for h in top_hits:
        stype = h.get("source_type", "")
        sid   = h.get("source_id", "")
        if stype and sid:
            by_type.setdefault(stype, []).append(sid)

    sf_records: dict[str, dict] = {}
    for stype, ids in by_type.items():
        sf_records.update(_structured_lookup(ids, stype))

    # Assemble final results
    results = []
    for h in top_hits:
        sid = h.get("source_id", "")
        results.append({
            "source_type":     h.get("source_type", ""),
            "source_id":       sid,
            "source_name":     h.get("metadata", {}).get("lcd_name")
                               or h.get("metadata", {}).get("ncd_title")
                               or h.get("metadata", {}).get("guideline_title")
                               or sid,
            "state_codes":     h.get("state_codes", []),
            "cpt_codes":       h.get("cpt_codes", []),
            "chunk_text":      h.get("metadata", {}).get("text", ""),
            "score":           h.get("score", 0.0),
            "snowflake_record": sf_records.get(sid),
        })

    return sorted(results, key=lambda r: r["score"], reverse=True)[:top_k]
