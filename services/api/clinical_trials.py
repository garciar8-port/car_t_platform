"""
ClinicalTrials.gov v2 API client for enriching BioFlow with real trial data.

Uses the public API (no key required): https://clinicaltrials.gov/api/v2/studies
Fetches active CAR-T cell therapy trials to populate realistic patient contexts.
"""

import httpx
from pydantic import BaseModel
from typing import Optional
import asyncio
from functools import lru_cache


CT_API_BASE = "https://clinicaltrials.gov/api/v2"


class ClinicalTrial(BaseModel):
    nct_id: str
    title: str
    status: str
    phase: str
    conditions: list[str]
    interventions: list[str]
    sponsor: str
    enrollment: Optional[int] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    locations: list[str] = []
    eligibility_criteria: Optional[str] = None


async def fetch_cart_trials(max_results: int = 20) -> list[ClinicalTrial]:
    """Fetch active CAR-T cell therapy trials from ClinicalTrials.gov."""
    params = {
        "query.term": "CAR-T cell therapy",
        "query.intr": "chimeric antigen receptor",
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING",
        "pageSize": min(max_results, 100),
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,Condition,InterventionName,LeadSponsorName,EnrollmentCount,StartDate,PrimaryCompletionDate,LocationFacility,EligibilityCriteria",
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{CT_API_BASE}/studies", params=params)
        resp.raise_for_status()
        data = resp.json()

    trials = []
    for study in data.get("studies", []):
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        design = proto.get("designModule", {})
        conditions_mod = proto.get("conditionsModule", {})
        interventions_mod = proto.get("armsInterventionsModule", {})
        sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
        enrollment_mod = proto.get("designModule", {}).get("enrollmentInfo", {})
        eligibility_mod = proto.get("eligibilityModule", {})
        contacts_mod = proto.get("contactsLocationsModule", {})

        # Extract locations
        locations = []
        for loc in (contacts_mod.get("locations", []) or []):
            facility = loc.get("facility", "")
            city = loc.get("city", "")
            state = loc.get("state", "")
            country = loc.get("country", "")
            if facility:
                locations.append(f"{facility}, {city}, {state} {country}".strip(", "))

        # Extract interventions
        interventions = []
        for arm in (interventions_mod.get("interventions", []) or []):
            name = arm.get("name", "")
            if name:
                interventions.append(name)

        trials.append(ClinicalTrial(
            nct_id=ident.get("nctId", ""),
            title=ident.get("briefTitle", ""),
            status=status_mod.get("overallStatus", ""),
            phase=(design.get("phases", [None]) or [None])[0] or "N/A",
            conditions=conditions_mod.get("conditions", []),
            interventions=interventions,
            sponsor=sponsor_mod.get("leadSponsor", {}).get("name", ""),
            enrollment=enrollment_mod.get("count"),
            start_date=status_mod.get("startDateStruct", {}).get("date"),
            completion_date=status_mod.get("primaryCompletionDateStruct", {}).get("date"),
            locations=locations[:5],  # Limit to first 5
            eligibility_criteria=eligibility_mod.get("eligibilityCriteria", ""),
        ))

    return trials


async def get_cart_indications() -> list[str]:
    """Get list of real indications from active CAR-T trials."""
    trials = await fetch_cart_trials(50)
    indications = set()
    for t in trials:
        for c in t.conditions:
            indications.add(c)
    return sorted(indications)


# Cache for demo use — avoids hitting the API on every page load
_trial_cache: list[ClinicalTrial] = []

async def get_cached_trials(max_results: int = 20) -> list[ClinicalTrial]:
    """Returns cached trials, fetching once on first call."""
    global _trial_cache
    if not _trial_cache:
        try:
            _trial_cache = await fetch_cart_trials(max_results)
        except Exception:
            _trial_cache = []  # Graceful fallback
    return _trial_cache
