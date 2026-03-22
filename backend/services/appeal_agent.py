"""
Vinci Appeal Generation Agent.

Agentic reasoning loop (max 5 iterations):
  Step 1 — Load CPB + identify exact denial criterion
  Step 2 — Decide retrieval strategy based on denial category
  Step 3 — Parallel: vector search (LCD/NCD/guidelines) + live PubMed + FDA + ClinicalTrials
  Step 4 — Check CCI/MUE for coding issues; check state law
  Step 5 — Synthesize → generate appeal letter via Gemini Flash

Tools available to the agent at each step:
  query_snowflake(sql)           — relational lookup
  vector_search(ns, query, k)   — semantic search
  fetch_pubmed(cpt, term)        — live PubMed (cached)
  fetch_fda(name)                — openFDA
  fetch_trials(cond, interv)     — ClinicalTrials.gov
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import google.generativeai as genai

from config import settings
from services.snowflake_client import query as sf_query
from services.vector_client import query as vec_query
from services.pubmed_client import search_pubmed
from services.openfda_client import search_drug, search_device
from services.clinicaltrials_client import search_trials
from services.gemini_client import generate_appeal_letter

genai.configure(api_key=settings.google_api_key)
_model = genai.GenerativeModel("gemini-1.5-flash")

MAX_ITERATIONS = 5

# ─── Tool implementations ─────────────────────────────────────────────────────

async def _tool_query_snowflake(sql: str) -> list[dict]:
    try:
        return sf_query(sql)
    except Exception as e:
        return [{"error": str(e)}]


async def _tool_vector_search(namespace: str, query: str, top_k: int = 6) -> list[dict]:
    try:
        results = vec_query(namespace, query, top_k=top_k)
        return [{"id": r["id"], "score": r["score"], "text": r["metadata"].get("text", ""), "meta": r["metadata"]} for r in results]
    except Exception as e:
        return [{"error": str(e)}]


async def _tool_fetch_pubmed(cpt_code: str, condition_term: str) -> list[dict]:
    try:
        return await search_pubmed(cpt_code, condition_term)
    except Exception as e:
        return [{"error": str(e)}]


async def _tool_fetch_fda(name: str, product_type: str = "drug") -> list[dict]:
    try:
        if product_type == "device":
            return await search_device(name)
        return await search_drug(name)
    except Exception as e:
        return [{"error": str(e)}]


async def _tool_fetch_trials(condition: str, intervention: str) -> list[dict]:
    try:
        return await search_trials(condition, intervention)
    except Exception as e:
        return [{"error": str(e)}]


TOOL_MAP = {
    "query_snowflake":  _tool_query_snowflake,
    "vector_search":    _tool_vector_search,
    "fetch_pubmed":     _tool_fetch_pubmed,
    "fetch_fda":        _tool_fetch_fda,
    "fetch_trials":     _tool_fetch_trials,
}

# ─── Agent prompt templates ───────────────────────────────────────────────────

_AGENT_SYSTEM = """\
You are the Vinci appeal generation agent. You have access to a set of tools to
retrieve evidence for building a prior authorization appeal letter.

Your goal: gather the strongest possible evidence to rebut the denial, then signal DONE.

Available tools (call them by returning JSON with "tool" and "args"):
  query_snowflake(sql)                      — query relational Snowflake tables:
      lcds, ncds, cci_edits, mue_edits, fda_products, state_regulations, cpbs
  vector_search(namespace, query, top_k)    — semantic search over:
      cpbs | lcds | ncds | guidelines | pubmed
  fetch_pubmed(cpt_code, condition_term)    — live PubMed search (cached)
  fetch_fda(name, product_type)             — openFDA: product_type = "drug" or "device"
  fetch_trials(condition, intervention)     — ClinicalTrials.gov completed studies

Respond with ONE of:
  A) A tool call:  {"tool": "tool_name", "args": {...}}
  B) Done signal:  {"done": true, "evidence_summary": "<structured summary of all evidence found>"}

Rules:
  - Never call the same tool with identical args twice
  - Prefer meta-analyses and RCTs over case series
  - Always check state_regulations for the patient's state
  - Always check cci_edits if multiple CPT codes are present
  - Maximum {max_iter} tool calls — be efficient
  - When you have enough evidence to write a compelling letter, return done
"""

_AGENT_STEP = """\
DENIAL CONTEXT:
{denial_json}

CPT CODE: {cpt_code}
CLINICAL NOTES: {clinical_notes}
PATIENT STATE: {patient_state}

TOOL RESULTS SO FAR:
{results_so_far}

ITERATION: {iteration}/{max_iter}

What tool should we call next to strengthen the appeal? Or are we done?
"""

# ─── Main agent loop ──────────────────────────────────────────────────────────

async def run_appeal_agent(
    denial: dict,
    cpt_code: str,
    clinical_notes: str,
    patient_state: str = "CA",
) -> dict:
    """
    Run the agentic retrieval loop, then generate the appeal letter.

    Returns:
      {
        "letter_text":    str,
        "citations":      [{"title", "url", "pmid"}],
        "fda_references": [{"product", "approval_date"}],
        "trials":         [{"nct_id", "title", "phase", "url"}],
        "evidence_summary": str,
        "generated_at":   str,
      }
    """
    system_prompt = _AGENT_SYSTEM.format(max_iter=MAX_ITERATIONS)
    results_log: list[dict] = []
    iteration = 0

    evidence_summary = ""

    while iteration < MAX_ITERATIONS:
        iteration += 1

        step_prompt = _AGENT_STEP.format(
            denial_json=json.dumps(denial, indent=2),
            cpt_code=cpt_code,
            clinical_notes=clinical_notes[:800],
            patient_state=patient_state,
            results_so_far=json.dumps(results_log[-6:], indent=2),  # last 6 results
            iteration=iteration,
            max_iter=MAX_ITERATIONS,
        )

        resp = _model.generate_content(system_prompt + "\n\n" + step_prompt)
        raw = resp.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            action = json.loads(raw)
        except json.JSONDecodeError:
            # Gemini returned prose instead of JSON — treat as done
            evidence_summary = raw
            break

        if action.get("done"):
            evidence_summary = action.get("evidence_summary", "")
            break

        tool_name = action.get("tool")
        args      = action.get("args", {})

        if tool_name not in TOOL_MAP:
            break

        tool_fn = TOOL_MAP[tool_name]
        tool_result = await tool_fn(**args)

        results_log.append({
            "tool": tool_name,
            "args": args,
            "result": tool_result,
        })

    # ── Extract structured citations from results_log ──────────────────────
    citations: list[dict]      = []
    fda_refs:  list[dict]      = []
    trials:    list[dict]      = []

    for entry in results_log:
        tool = entry["tool"]
        result = entry["result"]

        if tool == "fetch_pubmed" and isinstance(result, list):
            for art in result:
                if art.get("pmid"):
                    citations.append({
                        "title": art.get("title", ""),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{art['pmid']}/",
                        "pmid": art["pmid"],
                        "evidence_type": art.get("evidence_type", ""),
                        "journal": art.get("journal", ""),
                        "year": art.get("year"),
                    })

        elif tool == "fetch_fda" and isinstance(result, list):
            for prod in result:
                fda_refs.append({
                    "product": prod.get("brand") or prod.get("device_name", ""),
                    "approval_date": prod.get("approval_date") or prod.get("decision_date", ""),
                    "approval_type": prod.get("approval_type") or prod.get("clearance_type", ""),
                    "indications": prod.get("indications", "")[:500],
                })

        elif tool == "fetch_trials" and isinstance(result, list):
            for trial in result:
                trials.append({
                    "nct_id":  trial.get("nct_id", ""),
                    "title":   trial.get("title", ""),
                    "phase":   trial.get("phase", ""),
                    "url":     trial.get("url", ""),
                    "summary": trial.get("summary", "")[:300],
                })

    # ── Build evidence block for Gemini letter generation ─────────────────
    evidence_blocks: list[str] = []

    if citations:
        evidence_blocks.append("PUBMED EVIDENCE:")
        for c in citations[:6]:
            evidence_blocks.append(
                f"  [{c['evidence_type'].upper()}] {c['title']} — {c['journal']} ({c['year']}) PMID:{c['pmid']}"
            )

    if fda_refs:
        evidence_blocks.append("\nFDA REGULATORY DATA:")
        for f in fda_refs[:3]:
            evidence_blocks.append(
                f"  {f['product']} ({f['approval_type']}, approved {f['approval_date']})"
                f"\n  Indication: {f['indications'][:200]}"
            )

    if trials:
        evidence_blocks.append("\nCLINICAL TRIALS (COMPLETED):")
        for t in trials[:3]:
            evidence_blocks.append(f"  {t['nct_id']} Phase {t['phase']}: {t['title']}")

    # Add vector search results (LCD/NCD snippets)
    for entry in results_log:
        if entry["tool"] == "vector_search" and isinstance(entry["result"], list):
            ns = entry["args"].get("namespace", "")
            snippets = [r.get("text", "") for r in entry["result"][:3] if r.get("text")]
            if snippets:
                evidence_blocks.append(f"\n{ns.upper()} POLICY REFERENCES:")
                for s in snippets:
                    evidence_blocks.append(f"  …{s[:300]}…")

    evidence_text = "\n".join(evidence_blocks) or "Limited evidence retrieved — proceeding with available CPB context."

    # ── Generate the letter ────────────────────────────────────────────────
    from datetime import datetime
    letter_text = await generate_appeal_letter(
        denial=denial,
        clinical_notes=clinical_notes,
        evidence=evidence_text,
    )

    return {
        "letter_text":      letter_text,
        "citations":        citations,
        "fda_references":   fda_refs,
        "trials":           trials,
        "evidence_summary": evidence_summary,
        "generated_at":     datetime.utcnow().isoformat() + "Z",
    }
