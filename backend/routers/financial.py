from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from services.cost_lookup import lookup_procedure_cost
from services.nessie_client import simulate_scenarios

router = APIRouter()


class FinancialRequest(BaseModel):
    cpt_code: str
    deductible_remaining: float = 2000.0
    oop_max: float = 6000.0
    plan_type: str = "PPO"


class MonthPoint(BaseModel):
    month: int
    balance: float
    delta: float


class ScenarioResult(BaseModel):
    label: str
    description: str
    total_12m_cost: float
    final_balance: float
    trajectory: List[MonthPoint]
    color: str


class SimulationSummary(BaseModel):
    appeal_saves_vs_paying: float
    appeal_saves_vs_er: float
    best_case_savings: float
    monthly_patient_cost: float
    er_visit_cost: float


class FinancialSimulationResult(BaseModel):
    cpt_code: str
    procedure_cost: float
    monthly_drug_cost: float
    er_visit_cost: float
    cost_source: str
    customer_id: Optional[str]
    scenarios: Dict[str, ScenarioResult]
    summary: SimulationSummary


@router.post("/simulate", response_model=FinancialSimulationResult)
async def simulate(request: FinancialRequest):
    """
    Simulate three financial outcomes for a denied claim:
      A — Appeal & Win ($0 cost)
      B — Pay Out of Pocket (monthly cost × 12)
      C — Skip Treatment → ER Visit (single large charge at month 4)

    Uses CMS Physician Fee Schedule for procedure costs and
    Capital One Nessie API for account balance trajectory modeling.
    """
    # Step 1: look up real procedure/drug costs
    costs = await lookup_procedure_cost(request.cpt_code)

    # Step 2: run Nessie simulation
    try:
        result = await simulate_scenarios(
            procedure_cost=costs["procedure_cost"],
            monthly_drug_cost=costs["monthly_drug_cost"],
            er_visit_cost=costs["er_visit_cost"],
            deductible_remaining=request.deductible_remaining,
            oop_max=request.oop_max,
            plan_type=request.plan_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Financial simulation failed: {e}")

    return FinancialSimulationResult(
        cpt_code=request.cpt_code,
        procedure_cost=costs["procedure_cost"],
        monthly_drug_cost=costs["monthly_drug_cost"],
        er_visit_cost=costs["er_visit_cost"],
        cost_source=costs["source"],
        customer_id=result.get("customer_id"),
        scenarios={
            k: ScenarioResult(**v)
            for k, v in result["scenarios"].items()
        },
        summary=SimulationSummary(**result["summary"]),
    )


@router.get("/accounts")
async def list_accounts(customer_id: str):
    """Return Nessie accounts for a simulated customer."""
    import httpx
    from config import settings
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.nessie_base_url}/customers/{customer_id}/accounts",
                params={"key": settings.nessie_api_key},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
