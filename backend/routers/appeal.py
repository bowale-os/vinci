from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.appeal_agent import run_appeal_agent

router = APIRouter()


class DenialContext(BaseModel):
    patient_name: str
    claim_id: str
    denial_reason: str
    cpb_code_cited: str
    deadline: str
    required_docs: List[str]
    insurer_name: str
    denial_date: Optional[str] = None
    service_denied: Optional[str] = None
    denial_codes: Optional[List[str]] = None
    raw_text: Optional[str] = None


class AppealRequest(BaseModel):
    denial: DenialContext
    cpt_code: str
    clinical_notes: str
    patient_state: str = "CA"


class Citation(BaseModel):
    title: str
    url: str
    pmid: Optional[str] = None
    evidence_type: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None


class FDAReference(BaseModel):
    product: str
    approval_date: str
    approval_type: Optional[str] = None
    indications: Optional[str] = None


class Trial(BaseModel):
    nct_id: str
    title: str
    phase: str
    url: str
    summary: Optional[str] = None


class AppealLetter(BaseModel):
    letter_text: str
    citations: List[Citation]
    fda_references: List[FDAReference]
    trials: List[Trial]
    evidence_summary: str
    generated_at: str


class AudioRequest(BaseModel):
    letter_text: str


class AudioResponse(BaseModel):
    audio_url: str


class ReviseRequest(BaseModel):
    letter_text: str
    feedback: str
    denial_reason: Optional[str] = None
    insurer_name: Optional[str] = None


class ReviseResponse(BaseModel):
    letter_text: str


@router.post("/generate", response_model=AppealLetter)
async def generate_appeal(request: AppealRequest):
    """
    Run the Vinci appeal agent:
      1. Agentic loop: retrieves CPB, LCD/NCD, PubMed, FDA, ClinicalTrials, state law
      2. Synthesizes all evidence into a formal appeal letter via Gemini Flash
    """
    try:
        result = await run_appeal_agent(
            denial=request.denial.model_dump(),
            cpt_code=request.cpt_code,
            clinical_notes=request.clinical_notes,
            patient_state=request.patient_state,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Appeal generation failed: {e}")

    return AppealLetter(
        letter_text=result["letter_text"],
        citations=[Citation(**c) for c in result["citations"]],
        fda_references=[FDAReference(**f) for f in result["fda_references"]],
        trials=[Trial(**t) for t in result["trials"]],
        evidence_summary=result["evidence_summary"],
        generated_at=result["generated_at"],
    )


@router.post("/revise", response_model=ReviseResponse)
async def revise_appeal(request: ReviseRequest):
    """
    Revise an existing appeal letter based on user feedback.
    Preserves the formal structure and evidence while applying the requested changes.
    """
    from services.gemini_client import _model
    import re
    prompt = f"""You are revising a prior authorization appeal letter based on specific feedback from the patient.

ORIGINAL LETTER:
{request.letter_text}

DENIAL CONTEXT:
- Insurer: {request.insurer_name or "Not specified"}
- Denial reason: {request.denial_reason or "Not specified"}

USER FEEDBACK — what needs to change:
{request.feedback}

Instructions:
- Apply ONLY the changes described in the feedback. Do not rewrite sections that are not mentioned.
- Preserve all legal citations, evidence references, and formal structure.
- Keep the same 5-paragraph format and Times New Roman letter style.
- If the feedback corrects a factual error (wrong name, wrong date, wrong medication), fix it precisely.
- If the feedback asks to strengthen an argument, expand only that paragraph.
- Return only the revised letter text — no commentary, no explanation, no markdown."""

    try:
        resp = _model.generate_content([{"role": "user", "parts": [prompt]}])
        revised = resp.text.strip()
        revised = re.sub(r"^```(?:text)?\s*", "", revised)
        revised = re.sub(r"\s*```$", "", revised)
        return ReviseResponse(letter_text=revised)
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Revision failed: {e}")


@router.post("/audio", response_model=AudioResponse)
async def generate_audio(request: AudioRequest):
    """Convert appeal letter text to audio via ElevenLabs TTS."""
    from services.elevenlabs_client import synthesize_speech
    try:
        audio_url = await synthesize_speech(request.letter_text)
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {e}")
    return AudioResponse(audio_url=audio_url)
