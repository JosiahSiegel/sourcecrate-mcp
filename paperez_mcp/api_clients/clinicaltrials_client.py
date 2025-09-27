"""
ClinicalTrials.gov API client for clinical trial data search.
Enhanced medical research capability for trial data and protocols.
"""

import asyncio
import logging
import aiohttp
from typing import Any, Dict, List
from urllib.parse import quote_plus

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, config, api_status

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_clinicaltrials(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search ClinicalTrials.gov for clinical trial data"""
    cache_key = f"clinicaltrials:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # ClinicalTrials.gov API v2
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.term": query,
            "pageSize": limit,
            "format": "json",
            "fields": "NCTId,BriefTitle,OfficialTitle,Condition,Intervention,Phase,StudyType,PrimaryCompletionDate,LastUpdateSubmitDate,LeadSponsorName,OverallStatus,EnrollmentCount,EligibilityCriteria,StudyFirstSubmitDate,BriefSummary"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"ClinicalTrials.gov search failed with status {response.status}")
                    api_status["clinicaltrials"] = False
                    return []

                data = await response.json()
                studies = data.get("studies", [])

                results = []
                for study in studies:
                    try:
                        protocol_section = study.get("protocolSection", {})
                        identification_module = protocol_section.get("identificationModule", {})
                        status_module = protocol_section.get("statusModule", {})
                        sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
                        design_module = protocol_section.get("designModule", {})
                        conditions_module = protocol_section.get("conditionsModule", {})
                        description_module = protocol_section.get("descriptionModule", {})

                        nct_id = identification_module.get("nctId", "")
                        title = identification_module.get("briefTitle", "")

                        # Extract basic information safely
                        study_first_submit_date = status_module.get("studyFirstSubmitDate")
                        year = None
                        if study_first_submit_date and len(study_first_submit_date) >= 4:
                            try:
                                year = int(study_first_submit_date[:4])
                            except (ValueError, TypeError):
                                year = None

                        # Extract sponsor safely
                        lead_sponsor = sponsor_module.get("leadSponsor", {})
                        sponsor_name = lead_sponsor.get("name", "Unknown Sponsor") if isinstance(lead_sponsor, dict) else "Unknown Sponsor"

                        result = {
                            "title": title,
                            "authors": [sponsor_name],
                            "abstract": description_module.get("briefSummary", ""),
                            "journal": "ClinicalTrials.gov",
                            "year": year,
                            "nct_id": nct_id,
                            "doi": None,
                            "source": "ClinicalTrials.gov",
                            "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
                            "citation_count": 0,
                            # Clinical trial specific fields
                            "study_type": design_module.get("studyType", ""),
                            "overall_status": status_module.get("overallStatus", ""),
                            "conditions": conditions_module.get("conditions", []),
                            "last_update_date": status_module.get("lastUpdateSubmitDate", ""),
                            "lead_sponsor": sponsor_name,
                            # For consistency with other sources
                            "pdf_url": None,  # Clinical trials don't have PDFs in the traditional sense
                            "open_access_pdf": None
                        }
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"Error parsing study {study}: {e}")
                        continue

                # Cache for 1 hour
                cache.set(cache_key, results, expire=3600)
                logger.info(f"✅ ClinicalTrials.gov: Found {len(results)} clinical trials for '{query}'")
                return results

    except Exception as e:
        logger.warning(f"❌ ClinicalTrials.gov search failed: {e}")
        api_status["clinicaltrials"] = False
        return []


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_clinicaltrials_interventional(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search specifically for interventional clinical trials"""
    enhanced_query = f"{query} AND AREA[StudyType]Interventional"
    return await search_clinicaltrials(enhanced_query, limit)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_clinicaltrials_completed(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search specifically for completed clinical trials with results"""
    enhanced_query = f"{query} AND AREA[OverallStatus]Completed"
    return await search_clinicaltrials(enhanced_query, limit)