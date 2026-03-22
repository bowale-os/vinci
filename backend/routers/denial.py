import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional

log = logging.getLogger(__name__)

from services.documentai_client import parse_denial_document

router = APIRouter()

# Accepted upload extensions
_ACCEPTED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif",
    ".bmp", ".webp", ".gif", ".docx", ".doc", ".txt", ".odt", ".rtf",
}


class DenialParseResult(BaseModel):
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
    tldr: str = ""
    raw_text: str


@router.post("/parse", response_model=DenialParseResult)
async def parse_denial(file: UploadFile = File(...)):
    """
    Accept a denial letter in any common format (PDF, DOCX, DOC, image, TXT),
    run it through Document AI OCR, then extract structured fields via Gemini Flash.
    """
    filename = file.filename or "upload"
    from pathlib import Path
    ext = Path(filename).suffix.lower()

    if ext and ext not in _ACCEPTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Accepted: {', '.join(sorted(_ACCEPTED_EXTENSIONS))}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        fields = await parse_denial_document(filename, content)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {e}")

    return DenialParseResult(
        patient_name=fields.get("patient_name", "Unknown"),
        claim_id=fields.get("claim_id", "Unknown"),
        denial_reason=fields.get("denial_reason", "Not specified"),
        cpb_code_cited=fields.get("cpb_code_cited", "Not cited"),
        deadline=fields.get("deadline", "Not specified"),
        required_docs=fields.get("required_docs", []),
        insurer_name=fields.get("insurer_name", "Unknown"),
        denial_date=fields.get("denial_date"),
        service_denied=fields.get("service_denied"),
        denial_codes=fields.get("denial_codes"),
        tldr=fields.get("tldr", ""),
        raw_text=fields.get("raw_text", ""),
    )
