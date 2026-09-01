from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from github.schemas import GitHubAnalyzeRequest, GitHubAnalyzeResponse
from github.service import GitHubService
from github.security import clean_github_input, verify_ssrf_safe
from auth.deps import get_optional_current_user

github_router = APIRouter(prefix="/api/v1/github", tags=["GitHub"])
github_service = GitHubService()

@github_router.post("/analyze", response_model=GitHubAnalyzeResponse)
async def analyze_github_endpoint(
    payload: GitHubAnalyzeRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Validate and analyze a candidate's GitHub profile and public repositories.
    Returns technical depth score, hiring readiness score, repository audits, language breakdown, and quality recommendations.
    """
    user_id = current_user["_id"] if current_user else None

    # 1. Username / URL Input Validation
    try:
        clean_user = clean_github_input(payload.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Server-side SSRF Protection
    target_api_url = f"https://api.github.com/users/{clean_user}"
    if not verify_ssrf_safe(target_api_url):
        raise HTTPException(
            status_code=400,
            detail="Security Violation: Target GitHub request blocked due to SSRF safety policies."
        )

    # 3. Profile Fetch & Analysis
    try:
        result = await github_service.analyze_profile(clean_user, user_id=user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process GitHub profile analysis: {str(e)}")
