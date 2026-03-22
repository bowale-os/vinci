# Quick Setup — Vinci

Prior authorization automation app. FastAPI backend + Next.js frontend.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

---

## Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in env vars
cp .env.example .env
```

Edit `.env` with your API keys (see [Environment Variables](#environment-variables) below), then:

```bash
uvicorn main:app --reload
# Runs at http://localhost:8000
```

---

## Frontend

```bash
cd frontend

npm install

# Copy and fill in env vars
cp .env.local.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then:
```bash
npm run dev
# Runs at http://localhost:3000
```

---

## Environment Variables

### Backend `.env`

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini Flash API key |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID for Document AI |
| `DOCUMENT_AI_PROCESSOR_ID` | Document AI processor ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON |
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier |
| `SNOWFLAKE_USER` | Snowflake username |
| `SNOWFLAKE_PRIVATE_KEY_PATH` | Path to RSA private key (`.p8`) |
| `SNOWFLAKE_DATABASE` | Snowflake database name |
| `SNOWFLAKE_SCHEMA` | Snowflake schema name |
| `SNOWFLAKE_WAREHOUSE` | Snowflake warehouse name |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS API key |
| `CAPITAL_ONE_API_KEY` | Capital One Nessie API key |

### Frontend `.env.local`

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |

---

## API Health Check

```bash
curl http://localhost:8000/api/health
# {"status":"ok"}
```

---

## Deployment

| Layer | Platform | Notes |
|-------|---------|-------|
| Frontend | Vercel | Set `NEXT_PUBLIC_API_URL` to Railway backend URL |
| Backend | Railway | Dockerfile-based; set all env vars above in Railway dashboard |

```bash
# Frontend deploy
cd frontend && vercel

# Backend: push to Railway via GitHub or Railway CLI
railway up
```
