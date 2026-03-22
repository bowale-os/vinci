# TASKS

## Global Rules
- Always read PROJECT_OVERVIEW.md + ARCHITECTURE.md before starting a new feature.
- Before coding any task, write a subtask breakdown under that task and wait for confirmation.
- Only touch files explicitly listed for the current subtask unless the user approves more.
- For any frontend/UI task: generate a 21st.dev prompt first. Do not write UI code until user pastes the generated component back.
- After each subtask: mark it done with a one-line note on what changed.
- After all subtasks for a task: move the task to Done.

---

## Inbox

- [x] Task 1: Project Scaffolding — Initialize Next.js 14 frontend and FastAPI backend with folder structure, configs, and shared types.
- [x] Task 2: Environment & Config — Set up `.env.example` files for both frontend and backend with all required API key placeholders.
- [x] Task 3: FastAPI Core — done in Task 1.
- [x] Task 4: Snowflake Integration — Snowflake client, CPB router, Gemini scorer.
- [x] Task 5: Claim Matching API — 6-dimension specialist scoring via Gemini Flash.
- [x] Task 6: Denial Parsing API — Document AI multi-format + Gemini structured extraction.
- [x] Task 7: Appeal Generation API — Full data architecture: 9 Snowflake tables, Pinecone vector store, PubMed/FDA/ClinicalTrials live clients, 5-step reasoning agent, Gemini letter synthesis.
- [x] Task 8: Appeal Audio API — ElevenLabs TTS, base64 data URI, voice params, char limit guard.
- [x] Task 9: Financial Simulation API — CMS fee schedule cost lookup, 3-scenario Nessie simulation (appeal/pay/ER), 12-month balance trajectories.
- [x] Task 10: Landing Page UI — Hero, features grid, how-it-works, stats strip, CTA.
- [x] Task 11: Role Selection UI — Patient/Doctor cards with session persistence via VinciContext.
- [ ] Task 12: Dashboard UI — Build `/dashboard` showing active PA cases, status, and deadlines.
- [ ] Task 13: Claim Submission UI — Build `/submit` page with form, CPB match results display.
- [x] Task 14: Denial Parser UI — Drag-drop upload, contestable banner, plain-English explanation, overturn badge, deadline warning.
- [x] Task 15: Appeal Generator UI — `/appeal/letter` with sectioned letter preview, audio player, citations, download/copy, submission guide.
- [x] Task 16: Financial Simulation UI — `/appeal/financial` 3-scenario cards with mini line charts + `/appeal/rights` with IRO data and state law.
- [ ] Task 17: Deployment Config — Add `vercel.json`, Railway `Dockerfile`, and CI/CD notes.

---

## In Progress

(empty)

---

## Done

### Task 2: Environment & Config ✓
- `backend/.env` populated with Gemini + Nessie keys; Snowflake set up for key-pair auth (`snowflake_key.p8`).
- `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`.
- `.env.example` files for both; `next.config.mjs` updated; `config.py` switched from password to private key path.

### Task 1: Project Scaffolding ✓
- Next.js 14 (App Router, Tailwind, TS) scaffolded in `frontend/` with route stubs, axios API client, and shared types.
- FastAPI bootstrapped in `backend/` with CORS, health endpoint, and 4 modular routers (claim, denial, appeal, financial) with Pydantic models.
- `backend/config.py` with pydantic-settings for all external service credentials.
- `.gitignore` and `README.md` with full dev setup instructions added.
