from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any

from profile.schemas import UnifiedCandidateProfile, ProfileBuildRequest
from profile.service import candidate_profile_service
from auth.deps import get_current_user

profile_router = APIRouter(prefix="/api/v1/profile", tags=["Candidate Profile"])

@profile_router.get("", response_model=UnifiedCandidateProfile)
async def get_candidate_profile_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve the authenticated user's normalized Candidate Profile.
    Derives user identity strictly from JWT.
    """
    user_id = current_user["_id"]
    profile = await candidate_profile_service.get_or_create_profile(user_id, user_info=current_user)
    return profile

@profile_router.post("/build", response_model=UnifiedCandidateProfile)
async def build_candidate_profile_endpoint(
    payload: Optional[ProfileBuildRequest] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Synthesize and build a Unified Candidate Profile across available sources (Resume, LinkedIn, GitHub).
    Derives user identity strictly from JWT.
    """
    user_id = current_user["_id"]
    
    # Build updated unified candidate profile
    profile = await candidate_profile_service.build_profile(
        user_id=user_id,
        user_info=current_user
    )
    return profile

@profile_router.post("/refresh/{source}", response_model=UnifiedCandidateProfile)
async def refresh_candidate_source_endpoint(
    source: str,
    payload: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Refresh a single source channel (resume, linkedin, github) without wiping out other sources.
    Derives user identity strictly from JWT.
    """
    user_id = current_user["_id"]
    valid_sources = ["resume", "linkedin", "github"]
    source_clean = source.lower().strip()
    
    if source_clean not in valid_sources:
        raise HTTPException(status_code=400, detail=f"Invalid source '{source}'. Choose from {valid_sources}.")

    profile = await candidate_profile_service.refresh_source(
        user_id=user_id,
        source_name=source_clean,
        new_data=payload
    )
    return profile
