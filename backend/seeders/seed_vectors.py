"""
Embed text from Snowflake tables and upsert into MongoDB Atlas.

Namespaces:
  lcds        ← lcds.full_text        (with state_codes + cpt_codes filters)
  ncds        ← ncds.full_text        (national — no state filter)
  cpbs        ← cpbs.criteria
  guidelines  ← clinical_guidelines.recommendation_text
  pubmed      ← populated at query time

Run after seed_lcd_ncd.py (and other seeders) have completed.
"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.snowflake_client import query as sf_query
from services.vector_client import delete_namespace, embed, upsert

BATCH     = 5     # texts per Gemini embed call (free tier: 100 texts/min)
MAX_CHARS = 4000  # chars per chunk
OVERLAP   = 200   # overlap between chunks


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


def _chunk(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + MAX_CHARS, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += MAX_CHARS - OVERLAP
    return chunks


def _embed_and_upsert(
    namespace: str,
    rows: list[dict],
    text_field: str,
    id_field: str,
    meta_fields: list[str],
    source_type: str,
    state_field: str | None = None,
    cpt_field: str | None = None,
):
    if not rows:
        print(f"  '{namespace}' — no rows in Snowflake, skipping")
        return

    delete_namespace(namespace)

    vectors = []
    for row in rows:
        raw_text = str(row.get(text_field.upper()) or row.get(text_field) or "").strip()
        text     = _clean_html(raw_text)
        if not text:
            continue

        base_id = str(row.get(id_field.upper()) or row.get(id_field) or "")
        meta    = {f.lower(): str(row.get(f.upper()) or row.get(f) or "") for f in meta_fields}

        # Parse state/cpt codes stored as comma-separated strings
        state_codes: list[str] = []
        cpt_codes:   list[str] = []
        if state_field:
            raw = str(row.get(state_field.upper()) or row.get(state_field) or "")
            state_codes = [s.strip() for s in raw.split(",") if s.strip()]
        if cpt_field:
            raw = str(row.get(cpt_field.upper()) or row.get(cpt_field) or "")
            cpt_codes = [c.strip() for c in raw.split(",") if c.strip()]

        for i, chunk in enumerate(_chunk(text)):
            vectors.append({
                "id":          f"{base_id}_chunk{i}",
                "source_id":   base_id,
                "source_type": source_type,
                "state_codes": state_codes,
                "cpt_codes":   cpt_codes,
                "text":        chunk,
                "meta":        {**meta, "chunk_index": i, "source_id": base_id},
            })

    if not vectors:
        print(f"  '{namespace}' — rows present but no text content, skipping")
        return

    print(f"  Embedding {len(vectors):,} chunks for namespace '{namespace}' …")

    ok = err = 0
    for i in range(0, len(vectors), BATCH):
        batch = vectors[i: i + BATCH]
        texts = [v["text"] for v in batch]
        batch_num = i // BATCH
        for attempt in range(3):
            try:
                raw_emb = embed(texts)
                embeddings = [raw_emb] if isinstance(raw_emb[0], float) else raw_emb

                upsert(namespace, [
                    {
                        "id":          v["id"],
                        "source_id":   v["source_id"],
                        "source_type": v["source_type"],
                        "state_codes": v["state_codes"],
                        "cpt_codes":   v["cpt_codes"],
                        "values":      emb if isinstance(emb, list) else list(emb),
                        "metadata":    {**v["meta"], "text": v["text"][:500]},
                    }
                    for v, emb in zip(batch, embeddings)
                ])
                ok += len(batch)
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 35 + attempt * 10
                    print(f"    Batch {batch_num} rate limited — waiting {wait}s …")
                    time.sleep(wait)
                else:
                    print(f"    Batch {batch_num} error: {e}")
                    err += len(batch)
                    break
        time.sleep(3.5)  # 5 texts × ~17 batches/min = 85 texts/min, under 100 limit

    print(f"  '{namespace}' — {ok:,} vectors upserted ({err} errors) ✓")


def seed_lcds():
    rows = sf_query(
        "SELECT lcd_id, lcd_name, full_text, state_codes, cpt_codes "
        "FROM lcds WHERE full_text IS NOT NULL AND status = 'A'"
    )
    _embed_and_upsert(
        namespace="lcds", rows=rows,
        text_field="full_text", id_field="lcd_id",
        meta_fields=["lcd_name", "lcd_id"],
        source_type="lcd",
        state_field="state_codes",
        cpt_field="cpt_codes",
    )


def seed_ncds():
    rows = sf_query(
        "SELECT ncd_id, ncd_title, manual_section, full_text "
        "FROM ncds WHERE full_text IS NOT NULL"
    )
    _embed_and_upsert(
        namespace="ncds", rows=rows,
        text_field="full_text", id_field="ncd_id",
        meta_fields=["ncd_title", "manual_section", "ncd_id"],
        source_type="ncd",
    )


def seed_cpbs():
    rows = sf_query(
        "SELECT cpb_number, insurer_name, procedure_code, criteria "
        "FROM cpbs WHERE criteria IS NOT NULL"
    )
    _embed_and_upsert(
        namespace="cpbs", rows=rows,
        text_field="criteria", id_field="cpb_number",
        meta_fields=["insurer_name", "procedure_code", "cpb_number"],
        source_type="cpb",
    )


def seed_guidelines():
    rows = sf_query(
        "SELECT guideline_id, society, guideline_title, condition_category, "
        "recommendation_text, evidence_grade "
        "FROM clinical_guidelines WHERE recommendation_text IS NOT NULL"
    )
    _embed_and_upsert(
        namespace="guidelines", rows=rows,
        text_field="recommendation_text", id_field="guideline_id",
        meta_fields=["society", "guideline_title", "evidence_grade", "condition_category"],
        source_type="guideline",
    )


def seed_all():
    print("\nSeeding MongoDB vectors from Snowflake …")
    seed_lcds()
    seed_ncds()
    seed_cpbs()
    seed_guidelines()
    print("All vector namespaces seeded ✓\n")


if __name__ == "__main__":
    seed_all()
