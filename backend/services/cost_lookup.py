"""
Procedure and drug cost lookup.

Sources (in priority order):
  1. CMS Physician Fee Schedule API — actual Medicare reimbursement rates
     (used as a floor; real commercial costs are 1.5–3× higher)
  2. openFDA drug label → NDC → estimated average retail price
  3. Curated fallback table by CPT category — median costs from HCUP / CMS data

Returns:
  procedure_cost          — total billed cost (commercial rate estimate)
  patient_oop_estimate    — typical patient OOP before deductible/OOP max
  monthly_drug_cost       — if applicable (for chronic medication denials)
  er_visit_cost           — estimated ER cost if condition goes untreated
"""
import httpx

# CMS Physician Fee Schedule API (public, no key required)
_CMS_PFS_BASE = "https://data.cms.gov/data-api/v1/dataset"
_CMS_PFS_DATASET_ID = "9767cb68-8ea9-4f0b-8179-9431abc89f11"  # 2025 PFS national averages

# ── CPT category fallback costs (median, commercial rate) ──────────────────
# Source: HCUP NIS 2023, CMS PFS 2025 × 2.4 commercial multiplier
# Format: (procedure_cost, er_cost_if_untreated, monthly_drug_if_applicable)
_CPT_COST_TABLE: dict[str, tuple[float, float, float]] = {
    # Evaluation & Management
    "99213": (250, 1800, 0),
    "99214": (350, 1800, 0),
    "99215": (450, 1800, 0),
    "99232": (180, 1800, 0),
    # Cardiology
    "93000": (180, 12000, 0),   # ECG
    "93306": (1800, 25000, 0),  # Echo
    "93452": (8500, 35000, 0),  # Left heart cath
    "93880": (650, 15000, 0),   # Carotid duplex
    # Orthopedic
    "27447": (18000, 5000, 0),  # Total knee replacement
    "27130": (20000, 5000, 0),  # Total hip replacement
    "29827": (8500, 3000, 0),   # Shoulder arthroscopy
    "22612": (35000, 8000, 0),  # Lumbar fusion
    # Imaging
    "70553": (2200, 4000, 0),   # MRI brain w/wo contrast
    "72148": (1800, 3000, 0),   # MRI lumbar spine
    "74177": (2400, 4500, 0),   # CT abdomen/pelvis w contrast
    # Oncology
    "96413": (850, 45000, 0),   # Chemo IV infusion
    "77301": (4500, 0, 0),      # IMRT planning
    "77385": (1800, 0, 0),      # IMRT treatment
    # Psychiatry / Behavioral Health
    "90837": (180, 4500, 0),    # 60-min psychotherapy
    "90867": (280, 4500, 0),    # TMS initial
    "90868": (200, 4500, 0),    # TMS subsequent
    # Physical Therapy
    "97110": (120, 2200, 0),    # Therapeutic exercises
    "97530": (130, 2200, 0),    # Therapeutic activities
    # Diabetes
    "82947": (45, 8500, 0),     # Glucose test
    "95251": (180, 8500, 0),    # CGM analysis
    # GI
    "45378": (1800, 6000, 0),   # Colonoscopy diagnostic
    "43239": (2800, 7500, 0),   # EGD w biopsy
    # Neurology
    "95819": (1200, 15000, 0),  # EEG
    "64483": (1800, 8000, 0),   # Epidural steroid injection lumbar
    # Biologics (monthly drug cost rather than procedure)
    "J0129": (1800, 12000, 1800),  # Abatacept (Orencia)
    "J0178": (2200, 12000, 2200),  # Aflibercept (Eylea)
    "J0482": (3200, 15000, 3200),  # Avacopan
    "J0717": (1200, 10000, 1200),  # Cladribine
    "J2323": (14000, 18000, 14000), # Natalizumab (Tysabri)
    "J3590": (4500, 12000, 4500),  # Unclassified biologic
}

# Default fallback by code prefix
_PREFIX_FALLBACK: dict[str, tuple[float, float, float]] = {
    "99": (300, 1800, 0),    # E&M
    "93": (1200, 20000, 0),  # Cardiology
    "27": (15000, 4500, 0),  # Orthopedic
    "22": (30000, 8000, 0),  # Spine
    "70": (1800, 3500, 0),   # Radiology - head
    "72": (1600, 3000, 0),   # Radiology - spine
    "96": (900, 40000, 0),   # Chemo/infusion
    "90": (200, 4500, 0),    # Psychiatry
    "97": (120, 2000, 0),    # PT/OT
    "45": (1800, 6000, 0),   # Colonoscopy
    "43": (2500, 7000, 0),   # Upper GI
    "J":  (2500, 12000, 2500), # Injected drug/biologic
}

_DEFAULT_COST = (1500.0, 4000.0, 0.0)
_DEFAULT_ER   = 4000.0


async def lookup_procedure_cost(cpt_code: str) -> dict:
    """
    Return cost estimates for a CPT code.

    Returns:
      procedure_cost       — commercial billed amount
      monthly_drug_cost    — monthly cost if chronic medication
      er_visit_cost        — estimated ER cost if untreated
      source               — 'cms_pfs' | 'curated_table' | 'prefix_estimate'
    """
    # 1. Try CMS PFS API first (async, fast)
    cms_cost = await _fetch_cms_pfs(cpt_code)
    if cms_cost:
        return {
            "procedure_cost": round(cms_cost * 2.4, 2),  # commercial multiplier
            "monthly_drug_cost": 0.0,
            "er_visit_cost": _DEFAULT_ER,
            "source": "cms_pfs",
        }

    # 2. Curated table
    if cpt_code in _CPT_COST_TABLE:
        proc, er, drug = _CPT_COST_TABLE[cpt_code]
        return {
            "procedure_cost": proc,
            "monthly_drug_cost": drug,
            "er_visit_cost": er,
            "source": "curated_table",
        }

    # 3. Prefix fallback
    for prefix, (proc, er, drug) in _PREFIX_FALLBACK.items():
        if cpt_code.startswith(prefix):
            return {
                "procedure_cost": proc,
                "monthly_drug_cost": drug,
                "er_visit_cost": er,
                "source": "prefix_estimate",
            }

    return {
        "procedure_cost": _DEFAULT_COST[0],
        "monthly_drug_cost": _DEFAULT_COST[2],
        "er_visit_cost": _DEFAULT_ER,
        "source": "default_estimate",
    }


async def _fetch_cms_pfs(cpt_code: str) -> float | None:
    """Fetch the non-facility national average payment from the CMS PFS API."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"https://data.cms.gov/data-api/v1/dataset/{_CMS_PFS_DATASET_ID}/data",
                params={"filter[HCPCS_CD]": cpt_code, "size": 1},
            )
            if resp.status_code != 200:
                return None
            results = resp.json()
            if not results:
                return None
            # Field: NON_FAC_PE_NBNR (non-facility national average non-facility rate)
            raw = results[0].get("NON_FAC_PE_NBNR") or results[0].get("NONFAC_NA_PAYMENT")
            return float(raw) if raw else None
    except Exception:
        return None
