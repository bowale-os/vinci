"""
MongoDB Atlas Vector Search client.

Collection: <mongodb_database>.vectors
Document shape:
  {
    "_id"        : "<namespace>_<id>",
    "namespace"  : str,           — cpbs | lcds | ncds | guidelines | pubmed
    "source_id"  : str,           — original record ID (lcd_id, ncd_id, …)
    "source_type": str,           — "lcd" | "ncd" | "cpb" | "guideline" | "pubmed"
    "state_codes": [str],         — filterable: states this policy applies to
    "cpt_codes"  : [str],         — filterable: CPT/HCPCS codes
    "values"     : [float],       — 768-dim Gemini embedding
    "metadata"   : dict,          — display fields + text snippet
  }

Atlas Vector Search index (auto-created on first run):
  name: vector_index
  fields:
    vector  — path: values,      768 dims, cosine
    filter  — path: namespace
    filter  — path: state_codes
    filter  — path: cpt_codes
"""
from __future__ import annotations

from functools import lru_cache

import google.generativeai as genai
from pymongo import MongoClient, ReplaceOne

from config import settings

genai.configure(api_key=settings.google_api_key)

EMBED_MODEL = "models/gemini-embedding-001"
DIMENSION   = 768
COLLECTION  = "vectors"
INDEX_NAME  = "vector_index"

_INDEX_DEFINITION = {
    "name": INDEX_NAME,
    "type": "vectorSearch",
    "definition": {
        "fields": [
            {"type": "vector",  "path": "values",     "numDimensions": DIMENSION, "similarity": "cosine"},
            {"type": "filter",  "path": "namespace"},
            {"type": "filter",  "path": "state_codes"},
            {"type": "filter",  "path": "cpt_codes"},
        ]
    },
}


@lru_cache(maxsize=1)
def _get_collection():
    client = MongoClient(settings.mongodb_uri)
    db     = client[settings.mongodb_database]
    if COLLECTION not in db.list_collection_names():
        db.create_collection(COLLECTION)
        print(f"  Created collection '{COLLECTION}'")
    col = db[COLLECTION]
    existing = [idx["name"] for idx in col.list_search_indexes()]
    if INDEX_NAME not in existing:
        col.create_search_index(_INDEX_DEFINITION)
        print(f"  Created Atlas vector search index '{INDEX_NAME}' (building in background…)")
    return col


def embed(texts: list[str]) -> list[list[float]]:
    """Embed texts via gemini-embedding-001 (768-dim). Returns list of vectors."""
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=texts,
        task_type="retrieval_document",
        output_dimensionality=768,
    )
    emb = result["embedding"]
    # Single text returns a flat list; batch returns list of lists
    if isinstance(emb[0], float):
        return [emb]
    return emb


def upsert(namespace: str, vectors: list[dict]):
    """
    Upsert vectors into MongoDB.

    Each dict must have:
      id         — unique string ID
      values     — list[float] (768-dim)
      metadata   — dict (display fields + text snippet)

    Optional:
      source_id  — original record ID
      source_type— "lcd" | "ncd" | etc.
      state_codes— list[str]  (pre-filter field)
      cpt_codes  — list[str]  (pre-filter field)
    """
    col = _get_collection()
    ops = [
        ReplaceOne(
            {"_id": f"{namespace}_{v['id']}"},
            {
                "_id":         f"{namespace}_{v['id']}",
                "namespace":   namespace,
                "source_id":   v.get("source_id", v["id"]),
                "source_type": v.get("source_type", namespace.rstrip("s")),
                "state_codes": v.get("state_codes", []),
                "cpt_codes":   v.get("cpt_codes", []),
                "values":      v["values"],
                "metadata":    v["metadata"],
            },
            upsert=True,
        )
        for v in vectors
    ]
    if ops:
        col.bulk_write(ops, ordered=False)


def query(
    namespace: str,
    query_text: str,
    top_k: int = 8,
    filter: dict | None = None,
    state_code: str | None = None,
    cpt_codes: list[str] | None = None,
) -> list[dict]:
    """
    Semantic search over a namespace with optional pre-filters.

    Returns list of dicts: {id, score, metadata, state_codes, cpt_codes}
    """
    col   = _get_collection()
    q_vec = embed([query_text])[0]

    pre_filter: dict = {"namespace": {"$eq": namespace}}

    if state_code:
        pre_filter["state_codes"] = {"$eq": state_code}

    if cpt_codes:
        pre_filter["cpt_codes"] = {"$in": cpt_codes}

    if filter:
        pre_filter.update(filter)

    pipeline = [
        {"$vectorSearch": {
            "index":        INDEX_NAME,
            "path":         "values",
            "queryVector":  q_vec,
            "numCandidates": top_k * 10,
            "limit":         top_k,
            "filter":        pre_filter,
        }},
        {"$project": {
            "_id":         0,
            "id":          "$_id",
            "namespace":   1,
            "source_id":   1,
            "source_type": 1,
            "state_codes": 1,
            "cpt_codes":   1,
            "metadata":    1,
            "score":       {"$meta": "vectorSearchScore"},
        }},
    ]

    return list(col.aggregate(pipeline))


def delete_namespace(namespace: str):
    """Wipe all vectors in a namespace (safe if namespace doesn't exist yet)."""
    try:
        _get_collection().delete_many({"namespace": namespace})
    except Exception:
        pass
