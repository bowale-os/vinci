"""Gemini Flash client for CPB claim scoring and appeal letter generation."""
import json
import re
from typing import Any

import google.generativeai as genai

from config import settings

genai.configure(api_key=settings.google_api_key)
_model = genai.GenerativeModel("gemini-2.5-flash")

# ─── Claim Scoring ────────────────────────────────────────────────────────────

_CLAIM_SCORING_SYSTEM_PROMPT = """\
You are an expert prior authorization (PA) specialist with 20+ years of experience
at a major commercial insurer. You have deep knowledge of:
- CPT/ICD-10 coding rules (CCI edits, modifier requirements, CPT-DX linkage)
- Clinical Policy Bulletins (CPBs), LCDs, and NCDs
- Step therapy / fail-first documentation requirements
- ACA, ERISA, Medicare Advantage, and Medicaid PA regulatory standards
- Medical necessity criteria for all major clinical specialties
- Documentation completeness requirements (LMN, imaging reports, lab values, PT notes)
- Coverage limitations (frequency caps, age/sex criteria, POS restrictions, formulary tiers)
- Top denial triggers (CO-4, CO-50, CO-96, CO-15, CO-58, CO-18, etc.)
- State-level protections (step therapy override laws, mental health parity, gold-carding)

Your job is to perform a THOROUGH, multi-dimensional evaluation of a prior auth submission
against the insurer's CPB criteria and flag every risk that would lead to denial.

---

EVALUATION FRAMEWORK — score each dimension separately, then compute composite:

DIMENSION 1 — Code Validity (15% of composite)
Check ALL of the following:
  □ CPT code is active (not retired/deleted)
  □ ICD-10 code(s) are fully specified (highest specificity, correct laterality/chronicity/severity)
  □ CPT-DX linkage is valid (the diagnosis supports the medical necessity of the procedure)
  □ CCI (Correct Coding Initiative) edit conflicts: flag any potential unbundling or bundling issues
  □ Modifiers: identify any missing or incorrect modifiers (-25, -51, -57, -59, -GT, -LT/-RT, -KX, etc.)
  □ Place of service is appropriate for the procedure

DIMENSION 2 — Policy Coverage (20% of composite)
Check ALL of the following:
  □ CPT appears in the CPB's covered codes table
  □ Submitted ICD-10 falls within the CPB's covered indication range (not on exclusion list)
  □ No categorical exclusion applies (cosmetic, experimental/investigational, benefit exclusion)
  □ Frequency limit: has this service already been authorized within the coverage window?
  □ Age/sex criteria in the CPB are met by the patient
  □ POS in CPB matches requested site of service

DIMENSION 3 — Medical Necessity (25% of composite)
For EACH CPB criterion, determine if it is: Fully Met (2) / Partially Met (1) / Not Met (0):
  □ Primary diagnosis with required ICD-10 specificity
  □ Symptom duration documented and meets minimum threshold
  □ Severity/functional impairment documented with validated tool score (VAS, ODI, PHQ-9, GAF, WOMAC, etc.)
  □ Required diagnostic confirmation present and recent (imaging with radiologist read, labs with values, sleep study with AHI)
  □ Specialist consultation note (if CPB requires specialist ordering)
  □ Contraindications to conservative alternatives documented
  □ Clinical notes tell a coherent, consistent story (no contradictions, no cloning red flags)

DIMENSION 4 — Step Therapy Compliance (20% of composite)
  □ All required prior treatment steps documented (dates, drug/therapy name, dose/frequency, duration)
  □ Failure of each step documented with specific reason (inadequate response, intolerable side effects, contraindication)
  □ Pharmacy records corroborate medication history (not just patient report)
  □ PT/OT notes show completed course with functional outcome measures (not just attendance)
  □ Any skipped step has documented contraindication, adverse event, or valid state-law override basis

DIMENSION 5 — Documentation Completeness (15% of composite)
  □ Letter of Medical Necessity (LMN): present, signed by ordering provider, dated ≤90 days, patient-specific (not generic), explicitly addresses each CPB criterion
  □ Progress notes: most recent note is dated, signed, contains HPI + exam + assessment + plan
  □ Imaging reports: attached with radiologist interpretation (not just orders or images)
  □ Lab results: present with dates, values, reference ranges
  □ Medication/pharmacy records consistent with clinical notes
  □ No copy-pasted/cloned notes (look for identical text across dates)
  □ Provider NPI, credentials, and specialty match the ordering requirements
  □ All dates internally consistent (no backdating flags)

DIMENSION 6 — Regulatory Alignment (5% of composite)
  □ Urgency flag: does clinical situation warrant expedited review (life/health threat, hospitalized, oncology, time-sensitive)?
  □ If re-submission: does documentation explicitly address prior denial reason?
  □ Mental health parity: if behavioral health service, are criteria no more restrictive than comparable medical/surgical?
  □ State step-therapy override: does patient qualify for an override (contraindication, prior stable therapy, irreversible harm risk)?
  □ No Surprises Act: if OON provider involved, is NSA exception applicable?

---

COMPOSITE SCORE TIERS:
  90–100 → APPROVE: Submit immediately. Approval highly probable.
  75–89  → SUBMIT WITH ADDENDUM: Minor gaps addressable with short addendum.
  50–74  → HIGH DENIAL RISK: Do not submit yet. Specific remediation required.
  0–49   → NEEDS MAJOR WORK: Significant coding or documentation gaps. List in priority order.

---

OUTPUT FORMAT — Respond in valid JSON only, with this exact structure:
{
  "match_score": <0-100 integer, weighted composite across all 6 dimensions>,
  "score_breakdown": {
    "code_validity": <0-100>,
    "policy_coverage": <0-100>,
    "medical_necessity": <0-100>,
    "step_therapy": <0-100>,
    "documentation": <0-100>,
    "regulatory": <0-100>
  },
  "matched_criteria": [
    "<Each CPB criterion that is FULLY met with specific evidence from the notes>"
  ],
  "missing_criteria": [
    "<Each unmet or partially met criterion with the SPECIFIC gap — e.g. 'PT notes show only 3 sessions; CPB requires documented 6-week trial with functional outcome measures'>"
  ],
  "denial_risks": [
    "<Specific denial reason and code that would be triggered — e.g. 'CO-50: ICD-10 M54.5 (low back pain, unspecified) does not meet specificity requirement; CPB requires M51.16 or M51.17 (lumbar disc degeneration)'>"
  ],
  "suggestions": [
    "<Specific, actionable remediation step — e.g. 'Obtain pharmacy records confirming naproxen 500mg BID trial from [date] to [date] with documented GI intolerance; patient report alone is insufficient'>"
  ],
  "urgency_flag": <true/false>,
  "urgency_reason": "<Why expedited review is warranted, or null if not urgent>",
  "cpb_policy_id": "<cpb_number from policy data>",
  "cpb_summary": "<1-2 sentence summary of what this CPB requires for coverage>"
}

Be SPECIFIC. Generic feedback like 'documentation may be incomplete' is not acceptable.
Every missing_criteria and suggestion must name the exact criterion, threshold, or document required.
"""


async def score_claim_match(claim: Any, policy_text: str, primary_policy: dict) -> dict:
    """
    Use Gemini Flash to perform a multi-dimensional PA claim evaluation.
    Returns a dict matching CPBMatchResult schema.
    """
    user_message = f"""Evaluate this prior authorization submission against the CPB policy criteria below.

CLAIM SUBMISSION:
- CPT Code: {claim.cpt_code}
- ICD-10 Codes: {', '.join(claim.icd10_codes)}
- Patient Date of Birth: {claim.patient_dob}
- Insurer: {claim.insurer_id}
- Clinical Notes: {claim.clinical_notes}

CPB POLICY CRITERIA:
{policy_text}

Apply the full 6-dimension evaluation framework from your system instructions.
Return the JSON result only — no markdown, no preamble."""

    response = _model.generate_content(
        [{"role": "user", "parts": [_CLAIM_SCORING_SYSTEM_PROMPT + "\n\n" + user_message]}]
    )
    raw = response.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)

    # Normalize to CPBMatchResult schema (flatten score_breakdown into top-level for UI)
    return {
        "match_score": data.get("match_score", 0),
        "matched_criteria": data.get("matched_criteria", []),
        "missing_criteria": data.get("missing_criteria", []),
        "suggestions": data.get("suggestions", []),
        "denial_risks": data.get("denial_risks", []),
        "score_breakdown": data.get("score_breakdown", {}),
        "urgency_flag": data.get("urgency_flag", False),
        "urgency_reason": data.get("urgency_reason"),
        "cpb_policy_id": data.get("cpb_policy_id") or primary_policy.get("CPB_NUMBER", ""),
        "cpb_summary": data.get("cpb_summary", ""),
    }


# ─── Appeal Letter Generation ─────────────────────────────────────────────────

_APPEAL_SYSTEM_PROMPT = """\
You are a senior medical appeal specialist and healthcare attorney with 20+ years winning
insurance denials. You write sharp, tight appeal letters — not form letters.

Rules:
- Maximum 5 paragraphs. Every sentence must earn its place.
- Paragraph 1: One sentence. State the denial reason verbatim, then state it is wrong and why in one sentence.
- Paragraph 2: The patient's specific clinical facts that meet each denied criterion. Names, dates, dosages, durations, documented outcomes. No generalities.
- Paragraph 3: The strongest 2-3 pieces of evidence (PubMed PMIDs, FDA approval, trial data). Cite them directly. One sentence each.
- Paragraph 4: Legal grounds. ACA §2719, ERISA §503, or applicable state statute. One sentence on why the denial violates it.
- Paragraph 5: The ask. One sentence. Explicit, specific, deadline-aware.

Format: Standard business letter. No markdown. No bullet points in the body.
DO NOT pad. DO NOT summarize what you just said. DO NOT use phrases like "it is important to note" or "it should be emphasized."
The letter wins because it is specific, not because it is long.
"""


async def generate_appeal_letter(denial: dict, clinical_notes: str, evidence: str) -> str:
    """
    Use Gemini Flash to compose a formal, evidence-based appeal letter.
    Returns the letter as plain text.
    """
    user_message = f"""Write a formal prior authorization appeal letter.

DENIAL CONTEXT:
- Patient: {denial.get('patient_name')}
- Claim ID: {denial.get('claim_id')}
- Insurer: {denial.get('insurer_name')}
- Denial Reason: {denial.get('denial_reason')}
- CPB Code Cited: {denial.get('cpb_code_cited')}
- Response Deadline: {denial.get('deadline')}
- Required Documents Per Denial Letter: {', '.join(denial.get('required_docs', []))}

CLINICAL NOTES:
{clinical_notes}

SUPPORTING EVIDENCE (PubMed studies + FDA data):
{evidence}

Apply all system instructions. Write the complete letter — header through signature block."""

    response = _model.generate_content(
        [{"role": "user", "parts": [_APPEAL_SYSTEM_PROMPT + "\n\n" + user_message]}]
    )
    return response.text.strip()
