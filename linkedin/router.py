from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from linkedin.schemas import LinkedInAnalyzeRequest, LinkedInAnalyzeResponse
from linkedin.service import LinkedInService
from linkedin.security import validate_linkedin_url, verify_ssrf_safe
from auth.deps import get_optional_current_user

linkedin_router = APIRouter(prefix="/api/v1/linkedin", tags=["LinkedIn"])
linkedin_service = LinkedInService()

@linkedin_router.post("/analyze", response_model=LinkedInAnalyzeResponse)
async def analyze_linkedin_endpoint(
    payload: LinkedInAnalyzeRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Validate and analyze a public LinkedIn profile URL. Returns recruiter visibility score,
    sub-scores, headline review, about section critique, missing keywords, and optimization recommendations.
    """
    user_id = current_user["_id"] if current_user else None
    
    # 1. URL Format Validation
    try:
        clean_url = validate_linkedin_url(payload.profile_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Server-side SSRF Protection
    if not verify_ssrf_safe(clean_url):
        raise HTTPException(
            status_code=400,
            detail="Security Violation: The requested URL is prohibited due to SSRF safety policies."
        )

    # 3. Profile Fetch & Analysis
    try:
        result = await linkedin_service.analyze_profile(clean_url, user_id=user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process LinkedIn profile analysis: {str(e)}")
