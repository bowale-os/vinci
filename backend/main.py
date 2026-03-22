from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import claim, denial, appeal, financial

app = FastAPI(title="Vinci API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claim.router, prefix="/api/claim", tags=["claim"])
app.include_router(denial.router, prefix="/api/denial", tags=["denial"])
app.include_router(appeal.router, prefix="/api/appeal", tags=["appeal"])
app.include_router(financial.router, prefix="/api/financial", tags=["financial"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
