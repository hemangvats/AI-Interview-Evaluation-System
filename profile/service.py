from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any

from profile.db import profile_repo
from profile.schemas import (
    UnifiedCandidateProfile,
    SourceStatusMap,
    SourceTimestamps,
    ProfileBuildRequest
)
from profile.normalizer import normalize_candidate_sources

logger = logging.getLogger(__name__)

class CandidateProfileService:
    def __init__(self):
        self.repo = profile_repo

    async def get_or_create_profile(self, user_id: str, user_info: Optional[dict] = None) -> UnifiedCandidateProfile:
        """Fetch candidate profile from MongoDB; if absent, return clean initial profile."""
        doc = await self.repo.get_by_user_id(user_id)
        if doc:
            # Strip MongoDB ObjectId '_id'
            doc_copy = dict(doc)
            if "_id" in doc_copy:
                del doc_copy["_id"]
            return UnifiedCandidateProfile(**doc_copy)

        now_iso = datetime.now(timezone.utc).isoformat()
        name = user_info.get("name", "Candidate") if user_info else "Candidate"
        email = user_info.get("email", "") if user_info else ""

        init_profile = UnifiedCandidateProfile(
            user_id=user_id,
            identity={"name": name, "email": email},
            source_status=SourceStatusMap(),
            timestamps=SourceTimestamps(),
            created_at=now_iso,
            updated_at=now_iso
        )

        await self.repo.save_profile(user_id, init_profile.model_dump())
        return init_profile

    async def build_profile(
        self,
        user_id: str,
        resume_data: Optional[Dict[str, Any]] = None,
        linkedin_data: Optional[Dict[str, Any]] = None,
        github_data: Optional[Dict[str, Any]] = None,
        user_info: Optional[dict] = None
    ) -> UnifiedCandidateProfile:
        """
        Synthesize multi-source Candidate Profile from Resume, LinkedIn, and GitHub payloads.
        Supports partial source availability without requiring all three.
        """
        existing = await self.get_or_create_profile(user_id, user_info)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Update source payloads & statuses
        status_map = existing.source_status
        timestamps = existing.timestamps

        if resume_data:
            existing.resume = resume_data
            status_map.resume = "available"
            timestamps.resume_updated_at = now_iso

        if linkedin_data:
            existing.linkedin = linkedin_data
            status_map.linkedin = "available"
            timestamps.linkedin_updated_at = now_iso

        if github_data:
            existing.github = github_data
            status_map.github = "available"
            timestamps.github_updated_at = now_iso

        # Perform deterministic normalization across available sources
        (
            unified_skills,
            unified_exp,
            unified_edu,
            unified_proj,
            certs,
            consistency,
            strengths,
            gaps,
            recs
        ) = normalize_candidate_sources(existing.resume, existing.linkedin, existing.github)

        existing.unified_skills = unified_skills
        existing.unified_experience = unified_exp
        existing.unified_education = unified_edu
        existing.unified_projects = unified_proj
        existing.certifications = certs
        existing.consistency_report = consistency
        existing.strengths = strengths
        existing.gaps = gaps
        existing.recommendations = recs
        existing.source_status = status_map
        existing.timestamps = timestamps
        existing.updated_at = now_iso

        await self.repo.save_profile(user_id, existing.model_dump())
        return existing

    async def refresh_source(
        self,
        user_id: str,
        source_name: str,
        new_data: Optional[Dict[str, Any]] = None
    ) -> UnifiedCandidateProfile:
        """
        Refresh a single source (resume, linkedin, github) without wiping out other sources.
        """
        profile = await self.get_or_create_profile(user_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        source_name = source_name.lower()
        if source_name == "resume":
            profile.resume = new_data
            profile.source_status.resume = "available" if new_data else "not_provided"
            profile.timestamps.resume_updated_at = now_iso
        elif source_name == "linkedin":
            profile.linkedin = new_data
            profile.source_status.linkedin = "available" if new_data else "not_provided"
            profile.timestamps.linkedin_updated_at = now_iso
        elif source_name == "github":
            profile.github = new_data
            profile.source_status.github = "available" if new_data else "not_provided"
            profile.timestamps.github_updated_at = now_iso

        return await self.build_profile(
            user_id=user_id,
            resume_data=profile.resume,
            linkedin_data=profile.linkedin,
            github_data=profile.github
        )

candidate_profile_service = CandidateProfileService()
