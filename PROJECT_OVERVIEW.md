# Project Overview

## Problem
Prior authorization (PA) is one of healthcare's biggest bottlenecks. Patients are denied care due to mismatched CPB (Coverage Policy Bulletin) codes, denial letters are complex and opaque, appeals are rarely filed (and even more rarely won), and neither patients nor doctors have visibility into the financial stakes. Vinci automates the entire PA lifecycle — from claim submission to denial parsing to evidence-backed appeal generation — so that care is not delayed or denied due to administrative friction.

## Target Users
- **Patients**: Want to understand why a claim was denied, what an appeal looks like, and what it would cost them if the appeal fails.
- **Doctors / Care Teams**: Need to quickly match procedures to insurer CPB specs, generate compliant prior auth submissions, and craft appeals backed by clinical evidence.

## Core Features
1. **Prior Auth Claim Submission Matching** — Upload a procedure/diagnosis and match it against the insurer's CPB specifications using Snowflake (data warehouse) and Gemini Flash (AI matching & gap analysis).
2. **Denial Letter Parsing** — Upload a denial letter PDF; Google Document AI extracts structured fields (denial reason, CPB code cited, deadlines, required documentation).
3. **Appeal Letter Generation** — Auto-generate a personalized, evidence-backed appeal letter using PubMed (clinical evidence), openFDA (drug/device data), and ElevenLabs (audio version of the letter).
4. **Financial Impact Simulation** — Simulate the patient's out-of-pocket cost if the appeal fails, using Capital One Nessie API to model account impact and payment options.
5. **Dashboard** — Unified view for patients and doctors showing active PA cases, their status, deadlines, and outcomes.

## Non-Goals
- Real insurance portal integrations (EDI 278 submission) — all data is demo/mock or user-uploaded.
- HIPAA-compliant data storage at launch — data is ephemeral/session-based for hackathon scope.
- Full EHR integration (Epic, Cerner).
- Billing or payment processing.

## Tech Stack
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + TypeScript
- **Backend**: FastAPI (Python) deployed on Railway
- **Database**: Snowflake (CPB policy data, claim matching); no persistent user DB at launch
- **Auth**: None (demo mode) — role selected on login screen (Patient / Doctor)
- **AI / ML**: Google Gemini Flash (claim matching, gap analysis), Google Document AI (denial letter parsing)
- **Clinical Evidence**: PubMed E-utilities API, openFDA API
- **Audio**: ElevenLabs TTS (appeal letter audio)
- **Financial**: Capital One Nessie API (financial impact simulation)
- **Deployment**: Vercel (Next.js frontend), Railway (FastAPI backend)
