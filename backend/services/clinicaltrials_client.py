"""
ClinicalTrials.gov REST API v2 client.

Used to find completed trials supporting medical necessity of a procedure.
A completed Phase 3 or Phase 4 trial in the appeal is strong evidence that
the treatment is "standard of care" rather than experimental.
"""
import httpx

BASE = "https://clinicaltrials.gov/api/v2"


async def search_trials(condition: str, intervention: str, max_results: int = 5) -> list[dict]:
    """
    Search for completed trials by condition + intervention (drug/device/procedure).
    Returns list of trial summaries relevant for appeal letter citation.
    """
    params = {
        "query.cond": condition,
        "query.intr": intervention,
        "filter.overallStatus": "COMPLETED",
        "fields": "NCTId,BriefTitle,Condition,InterventionName,Phase,StartDate,CompletionDate,BriefSummary,PrimaryOutcomeDescription",
        "pageSize": max_results,
        "sort": "LastUpdatePostDate:desc",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{BASE}/studies", params=params)
        if resp.status_code != 200:
            return []
        studies = resp.json().get("studies", [])

    results = []
    for s in studies:
        proto = s.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status = proto.get("statusModule", {})
        desc   = proto.get("descriptionModule", {})
        design = proto.get("designModule", {})

        phases = design.get("phases", [])
        phase_str = "/".join(phases) if phases else "N/A"

        results.append({
            "nct_id": ident.get("nctId", ""),
            "title": ident.get("briefTitle", "")[:500],
            "conditions": proto.get("conditionsModule", {}).get("conditions", []),
            "interventions": [
                i.get("interventionName", "")
                for i in proto.get("armsInterventionsModule", {}).get("interventions", [])
            ][:3],
            "phase": phase_str,
            "start_date": status.get("startDateStruct", {}).get("date", ""),
            "completion_date": status.get("completionDateStruct", {}).get("date", ""),
            "summary": desc.get("briefSummary", "")[:1000],
            "url": f"https://clinicaltrials.gov/study/{ident.get('nctId', '')}",
        })

    return results
