"""
Capital One Nessie API client.

Creates a mock customer + account, then simulates 12-month transaction
histories for three denial-outcome scenarios:

  Scenario A — Appeal & Win
    No out-of-pocket cost. Account balance unchanged. One small admin fee.

  Scenario B — Give Up & Pay Out of Pocket
    Monthly treatment cost deducted every month for 12 months.
    Shows cumulative depletion of account balance.

  Scenario C — Skip Treatment → ER Visit
    No monthly cost until month 4, then a single large ER charge.
    Often more expensive than 12 months of treatment combined.

Each scenario returns a month-by-month account balance trajectory
(13 points: month 0 through month 12) for frontend chart rendering.
"""
import asyncio
import uuid
from datetime import date, timedelta
from typing import Optional

import httpx

from config import settings

_BASE = settings.nessie_base_url
_KEY  = settings.nessie_api_key
_STARTING_BALANCE = 5000.0   # demo patient starting balance


# ── Nessie API helpers ────────────────────────────────────────────────────────

async def _post(client: httpx.AsyncClient, path: str, body: dict) -> dict:
    resp = await client.post(
        f"{_BASE}{path}",
        params={"key": _KEY},
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


async def _get(client: httpx.AsyncClient, path: str) -> dict | list:
    resp = await client.get(
        f"{_BASE}{path}",
        params={"key": _KEY},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


async def _create_customer(client: httpx.AsyncClient) -> str:
    """Create a Nessie demo customer and return their customer_id."""
    data = await _post(client, "/customers", {
        "first_name": "Vinci",
        "last_name":  "DemoPatient",
        "address": {
            "street_number": "123",
            "street_name":   "Health St",
            "city":          "Nashville",
            "state":         "TN",
            "zip":           "37201",
        },
    })
    return data.get("objectCreated", {}).get("_id") or data.get("_id", str(uuid.uuid4()))


async def _create_account(client: httpx.AsyncClient, customer_id: str, label: str) -> str:
    """Create a checking account for the customer and return account_id."""
    data = await _post(client, f"/customers/{customer_id}/accounts", {
        "type":    "Checking",
        "nickname": label,
        "rewards": 0,
        "balance": _STARTING_BALANCE,
    })
    return data.get("objectCreated", {}).get("_id") or data.get("_id", str(uuid.uuid4()))


async def _post_purchase(
    client: httpx.AsyncClient,
    account_id: str,
    amount: float,
    description: str,
    purchase_date: str,
) -> None:
    """Record a purchase (debit) transaction against an account."""
    try:
        await _post(client, f"/accounts/{account_id}/purchases", {
            "merchant_id":   "56cdd68fa73e494d8675ec49",  # Nessie demo merchant
            "medium":        "balance",
            "purchase_date": purchase_date,
            "amount":        round(amount, 2),
            "description":   description,
            "status":        "completed",
        })
    except Exception:
        pass  # Non-fatal — simulation continues with calculated balance


# ── Scenario simulation ───────────────────────────────────────────────────────

def _build_trajectory(
    starting: float,
    monthly_deductions: list[float],   # index 0 = month 1 deduction
) -> list[dict]:
    """
    Build a 13-point balance trajectory (month 0 → month 12).
    Returns list of {month, balance, delta} dicts.
    """
    trajectory = [{"month": 0, "balance": round(starting, 2), "delta": 0.0}]
    balance = starting
    for i, deduction in enumerate(monthly_deductions, start=1):
        balance = max(0.0, balance - deduction)
        trajectory.append({
            "month":   i,
            "balance": round(balance, 2),
            "delta":   round(-deduction, 2),
        })
    return trajectory


async def _seed_nessie_transactions(
    account_id: str,
    scenario: str,
    monthly_cost: float,
    er_cost: float,
    er_month: int,
) -> None:
    """Post actual transactions to Nessie for a scenario (best effort)."""
    today = date.today()
    async with httpx.AsyncClient() as client:
        if scenario == "B":
            for m in range(1, 13):
                tx_date = (today + timedelta(days=30 * m)).isoformat()
                await _post_purchase(client, account_id, monthly_cost,
                                     f"Treatment Month {m}", tx_date)
        elif scenario == "C":
            tx_date = (today + timedelta(days=30 * er_month)).isoformat()
            await _post_purchase(client, account_id, er_cost,
                                 "Emergency Room Visit", tx_date)


# ── Public API ────────────────────────────────────────────────────────────────

async def simulate_scenarios(
    procedure_cost: float,
    monthly_drug_cost: float,
    er_visit_cost: float,
    deductible_remaining: float,
    oop_max: float,
    plan_type: str = "PPO",
) -> dict:
    """
    Run three financial scenarios and return trajectories + summary stats.

    Returns:
      customer_id, account_ids, scenarios (A/B/C with trajectory + stats)
    """
    # Determine actual patient cost after deductible/OOP max
    effective_cost = procedure_cost if not monthly_drug_cost else monthly_drug_cost

    # What the patient pays OOP (capped at OOP max)
    patient_oop_annual = min(
        max(0.0, effective_cost - max(0.0, oop_max - deductible_remaining)),
        oop_max,
    )
    monthly_patient_cost = round(
        (monthly_drug_cost if monthly_drug_cost else procedure_cost) * 0.25,  # 25% coinsurance
        2
    )
    monthly_patient_cost = min(monthly_patient_cost, oop_max / 12)

    # ── Create Nessie customer + 3 accounts (one per scenario) ────────────
    customer_id  = None
    account_ids  = {}
    nessie_ok    = bool(settings.nessie_api_key)

    if nessie_ok:
        try:
            async with httpx.AsyncClient() as client:
                customer_id = await _create_customer(client)
                for label in ("A_appeal_win", "B_pay_oop", "C_skip_er"):
                    account_ids[label] = await _create_account(client, customer_id, label)
        except Exception:
            nessie_ok = False

    # ── Build trajectories ─────────────────────────────────────────────────

    # Scenario A — Appeal & Win: $0 impact, one $15 admin/mailing fee
    deductions_a = [15.0] + [0.0] * 11
    traj_a = _build_trajectory(_STARTING_BALANCE, deductions_a)

    # Scenario B — Pay Out of Pocket: monthly cost every month
    monthly_b    = monthly_patient_cost if monthly_drug_cost else round(procedure_cost * 0.20, 2)
    deductions_b = [monthly_b] * 12
    traj_b       = _build_trajectory(_STARTING_BALANCE, deductions_b)

    # Scenario C — Skip Treatment → ER at month 4
    er_month = 4
    deductions_c = [0.0] * 12
    deductions_c[er_month - 1] = er_visit_cost
    traj_c = _build_trajectory(_STARTING_BALANCE, deductions_c)

    # ── Post transactions to Nessie (fire-and-forget) ─────────────────────
    if nessie_ok and account_ids:
        asyncio.create_task(
            _seed_nessie_transactions(
                account_ids.get("B_pay_oop", ""),
                "B", monthly_b, er_visit_cost, er_month,
            )
        )
        asyncio.create_task(
            _seed_nessie_transactions(
                account_ids.get("C_skip_er", ""),
                "C", monthly_b, er_visit_cost, er_month,
            )
        )

    # ── Compute summary stats ──────────────────────────────────────────────
    total_cost_b = sum(deductions_b)
    total_cost_c = er_visit_cost
    savings_vs_b = round(total_cost_b - 15.0, 2)
    savings_vs_c = round(total_cost_c - 15.0, 2)
    best_savings = max(savings_vs_b, savings_vs_c)

    return {
        "customer_id": customer_id,
        "account_ids": account_ids,
        "starting_balance": _STARTING_BALANCE,
        "scenarios": {
            "A": {
                "label":          "Appeal & Win",
                "description":    "Submit the Vinci appeal letter. If approved, you pay $0 for treatment.",
                "total_12m_cost": 15.0,
                "trajectory":     traj_a,
                "final_balance":  traj_a[-1]["balance"],
                "color":          "#22c55e",  # green
            },
            "B": {
                "label":          "Give Up & Pay Out of Pocket",
                "description":    f"Pay ${monthly_b:,.0f}/month for treatment without insurance coverage.",
                "total_12m_cost": round(total_cost_b, 2),
                "trajectory":     traj_b,
                "final_balance":  traj_b[-1]["balance"],
                "color":          "#f97316",  # orange
            },
            "C": {
                "label":          "Skip Treatment → ER Visit",
                "description":    f"Avoid costs until symptoms escalate. Estimated ER visit at month {er_month}: ${er_visit_cost:,.0f}.",
                "total_12m_cost": round(total_cost_c, 2),
                "trajectory":     traj_c,
                "final_balance":  traj_c[-1]["balance"],
                "color":          "#ef4444",  # red
            },
        },
        "summary": {
            "appeal_saves_vs_paying":     savings_vs_b,
            "appeal_saves_vs_er":         savings_vs_c,
            "best_case_savings":          best_savings,
            "monthly_patient_cost":       monthly_b,
            "er_visit_cost":              er_visit_cost,
        },
    }
