# Architecture

## Pages & Routes

### Next.js Frontend (Vercel)
| Path | Purpose |
|------|---------|
| `/` | Landing page — hero, features overview, CTA to enter as Patient or Doctor |
| `/role` | Role selection screen — choose Patient or Doctor, sets session context |
| `/dashboard` | Unified dashboard — active PA cases, status badges, deadlines |
| `/submit` | Prior auth claim submission — upload procedure/diagnosis, match against CPB specs |
| `/denial` | Denial letter upload & parsing — upload PDF, view extracted structured data |
| `/appeal` | Appeal letter generation — view generated letter, download PDF, play audio |
| `/financial` | Financial impact simulation — out-of-pocket cost projection, account impact chart |

---

## API Endpoints

### FastAPI Backend (Railway) — base: `https://vinci-api.railway.app`

#### Claim Matching
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/claim/match` | Accept procedure code (CPT), diagnosis (ICD-10), insurer ID. Query Snowflake for CPB specs. Use Gemini Flash to score match and identify gaps. Returns match score, missing fields, suggestions. |
| GET | `/api/claim/insurers` | Return list of supported insurers and their CPB policy IDs available in Snowflake. |

#### Denial Parsing
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/denial/parse` | Accept denial letter PDF (multipart). Send to Google Document AI. Return structured fields: denial_reason, cpb_code, deadline, required_docs, patient_name, claim_id. |

#### Appeal Generation
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/appeal/generate` | Accept denial parse result + patient/procedure context. Query PubMed for supporting studies. Query openFDA for drug/device approval data. Use Gemini Flash to compose appeal letter. Return letter text + citations. |
| POST | `/api/appeal/audio` | Accept appeal letter text. Send to ElevenLabs TTS. Return audio URL or base64 MP3. |

#### Financial Simulation
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/financial/simulate` | Accept procedure cost estimate, patient plan deductible/OOP max. Call Capital One Nessie API to model account impact. Return monthly payment options, total OOP projection, savings shortfall. |
| GET | `/api/financial/accounts` | Return mock Nessie accounts for demo patient. |

#### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Returns `{ status: "ok" }` |

---

## Data Models

### ClaimSubmission
```
{
  cpt_code: string,           // e.g. "99213"
  icd10_codes: string[],      // e.g. ["J45.50"]
  insurer_id: string,         // e.g. "BCBS_TN"
  patient_dob: string,        // "YYYY-MM-DD"
  clinical_notes: string      // free text
}
```

### CPBMatchResult
```
{
  match_score: number,        // 0-100
  matched_criteria: string[],
  missing_criteria: string[],
  suggestions: string[],
  cpb_policy_id: string,
  cpb_summary: string
}
```

### DenialParseResult
```
{
  patient_name: string,
  claim_id: string,
  denial_reason: string,
  cpb_code_cited: string,
  deadline: string,           // ISO date
  required_docs: string[],
  insurer_name: string,
  raw_text: string
}
```

### AppealLetter
```
{
  letter_text: string,
  citations: { title: string, url: string, pmid?: string }[],
  fda_references: { product: string, approval_date: string }[],
  generated_at: string        // ISO timestamp
}
```

### FinancialSimulation
```
{
  procedure_cost: number,
  patient_responsibility: number,
  deductible_remaining: number,
  oop_max_remaining: number,
  monthly_options: { months: number, payment: number }[],
  account_impact: { account_id: string, balance_after: number }[]
}
```

---

## Auth & Permissions

No authentication for hackathon scope. On `/role` selection:
- A `role` cookie/localStorage value is set (`"patient"` or `"doctor"`)
- The dashboard and feature pages adapt their UI and copy to the selected role
- Doctor view shows CPB gap analysis details; Patient view emphasizes plain-language summaries and financial impact

---

## External Services

| Service | Purpose | Integration Point |
|---------|---------|------------------|
| **Snowflake** | Stores CPB policy specifications per insurer; queried for claim matching | FastAPI `/api/claim/match` via `snowflake-connector-python` |
| **Google Gemini Flash** | AI reasoning for CPB match scoring, gap analysis, appeal letter composition | FastAPI via `google-generativeai` SDK |
| **Google Document AI** | OCR + structured extraction from denial letter PDFs | FastAPI `/api/denial/parse` via `google-cloud-documentai` |
| **PubMed E-utilities** | Fetch clinical studies supporting the appeal | FastAPI `/api/appeal/generate` via HTTP REST |
| **openFDA** | Drug/device approval data for appeal evidence | FastAPI `/api/appeal/generate` via HTTP REST |
| **ElevenLabs** | Text-to-speech for appeal letter audio | FastAPI `/api/appeal/audio` via `elevenlabs` SDK |
| **Capital One Nessie** | Mock banking API for financial impact simulation | FastAPI `/api/financial/simulate` via HTTP REST |

---

## Deployment

| Layer | Platform | Notes |
|-------|---------|-------|
| Frontend | **Vercel** | `NEXT_PUBLIC_API_URL` env var points to Railway backend |
| Backend | **Railway** | Dockerfile-based FastAPI app; env vars for all API keys |
| Snowflake | **Snowflake Cloud** | Connection credentials in Railway env vars |
