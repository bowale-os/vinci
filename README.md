# Vinci

Healthtech web app that automates the prior authorization lifecycle — from CPB-compliant claim submission to denial letter parsing, evidence-backed appeal generation, and financial impact simulation.

## Stack
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + TypeScript → deployed on Vercel
- **Backend**: FastAPI (Python) → deployed on Railway
- **AI**: Google Gemini Flash, Google Document AI
- **Data**: Snowflake (CPB policies)
- **Clinical Evidence**: PubMed, openFDA
- **Audio**: ElevenLabs TTS
- **Financial**: Capital One Nessie API

## Local Development

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill in your API keys
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL
npm run dev
```

Frontend runs at `http://localhost:3000`, backend at `http://localhost:8000`.

## Project Structure
```
vandyhacks/
├── frontend/          # Next.js 14 app
│   ├── app/           # App Router pages
│   ├── lib/           # API client
│   └── types/         # Shared TypeScript interfaces
├── backend/           # FastAPI app
│   ├── main.py        # App entry point
│   ├── config.py      # Settings / env vars
│   └── routers/       # Feature routers
├── PROJECT_OVERVIEW.md
├── ARCHITECTURE.md
└── TASKS.md
```
