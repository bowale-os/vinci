from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from services.snowflake_client import query as sf_query

router = APIRouter()


# ─── Pydantic models ──────────────────────────────────────────────────────────

class ClaimSubmission(BaseModel):
    cpt_code: str
    icd10_codes: List[str]
    insurer_id: str
    patient_dob: str
    clinical_notes: str


class ScoreBreakdown(BaseModel):
    code_validity: float = 0
    policy_coverage: float = 0
    medical_necessity: float = 0
    step_therapy: float = 0
    documentation: float = 0
    regulatory: float = 0


class CPBMatchResult(BaseModel):
    match_score: float
    score_breakdown: ScoreBreakdown
    matched_criteria: List[str]
    missing_criteria: List[str]
    denial_risks: List[str]
    suggestions: List[str]
    urgency_flag: bool = False
    urgency_reason: Optional[str] = None
    cpb_policy_id: str
    cpb_summary: str


class Insurer(BaseModel):
    id: str
    name: str
    cpb_number: str
    procedure_code: str


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/insurers", response_model=List[Insurer])
async def list_insurers():
    """Return distinct insurers from the Snowflake cpbs table."""
    rows = sf_query(
        "SELECT DISTINCT insurer_name, cpb_number, procedure_code FROM cpbs ORDER BY insurer_name"
    )
    return [
        Insurer(
            id=r["INSURER_NAME"].lower().replace(" ", "_"),
            name=r["INSURER_NAME"],
            cpb_number=r["CPB_NUMBER"],
            procedure_code=r["PROCEDURE_CODE"],
        )
        for r in rows
    ]


@router.get("/policies")
async def list_policies(procedure_code: str | None = None, insurer_name: str | None = None):
    """Return CPB policies, optionally filtered by procedure code or insurer."""
    sql = "SELECT * FROM cpbs WHERE 1=1"
    params: list = []
    if procedure_code:
        sql += " AND procedure_code = %s"
        params.append(procedure_code)
    if insurer_name:
        sql += " AND insurer_name = %s"
        params.append(insurer_name)
    sql += " ORDER BY last_updated DESC"
    return sf_query(sql, tuple(params))


@router.post("/match", response_model=CPBMatchResult)
async def match_claim(claim: ClaimSubmission):
    """Match a claim against CPB specs via Snowflake lookup + Gemini Flash scoring."""
    # Fetch matching policies for this procedure code from Snowflake
    rows = sf_query(
        "SELECT * FROM cpbs WHERE procedure_code = %s ORDER BY last_updated DESC LIMIT 5",
        (claim.cpt_code,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No CPB policies found for CPT {claim.cpt_code}")

    # Build context for Gemini
    policy_text = "\n\n".join(
        f"Policy {r['CPB_NUMBER']} ({r['INSURER_NAME']}):\n{r['CRITERIA']}" for r in rows
    )

    from services.gemini_client import score_claim_match  # lazy import
    result = await score_claim_match(claim, policy_text, rows[0])
    return result
