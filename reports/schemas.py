from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

class SkillValidationStatus(str, Enum):
    DEMONSTRATED = "Demonstrated"
    PARTIALLY_DEMONSTRATED = "Partially Demonstrated"
    NOT_ASSESSED = "Not Assessed"

class SkillValidationItem(BaseModel):
    skill: str
    profile_sources: List[str] = []
    interview_evidence: str = "Not assessed during this session"
    status: SkillValidationStatus = SkillValidationStatus.NOT_ASSESSED

class ProjectValidationStatus(str, Enum):
    DEMONSTRATED = "Demonstrated"
    PARTIALLY_DEMONSTRATED = "Partially Demonstrated"
    NOT_ASSESSED = "Not Assessed"

class ProjectValidationItem(BaseModel):
    project_title: str
    profile_sources: List[str] = []
    interview_evidence: str = "Not discussed during interview"
    status: ProjectValidationStatus = ProjectValidationStatus.NOT_ASSESSED

class CandidateOverview(BaseModel):
    candidate_name: str = "Candidate"
    target_role: str = "Software Engineer"
    interview_date: str = ""
    source_status: Dict[str, str] = {
        "resume": "not_provided",
        "linkedin": "not_provided",
        "github": "not_provided"
    }
    has_profile: bool = False

class ProfileEvidenceSummary(BaseModel):
    resume_ats_score: Optional[int] = None
    resume_strengths: List[str] = []
    resume_weaknesses: List[str] = []
    
    linkedin_score: Optional[int] = None
    linkedin_visibility_score: Optional[int] = None
    linkedin_headline_suggestion: str = ""
    
    github_score: Optional[int] = None
    github_technical_depth: Optional[int] = None
    github_hiring_readiness: Optional[int] = None

class InterviewPerformanceSummary(BaseModel):
    interview_score: Optional[float] = None
    total_exchanges: int = 0
    hiring_decision: str = "Pending"
    verdict_reasoning: str = ""
    difficulty_progression: List[str] = []
    final_summary_markdown: str = ""

class ConsistencyReport(BaseModel):
    consistent_claims: List[str] = []
    limited_evidence_claims: List[str] = []
    discrepancy_notes: List[str] = []

class UnifiedCandidateReport(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    created_at: str = ""
    overview: CandidateOverview
    interview_performance: InterviewPerformanceSummary
    profile_evidence: ProfileEvidenceSummary
    skill_validation: List[SkillValidationItem] = []
    project_validation: List[ProjectValidationItem] = []
    consistency_analysis: ConsistencyReport = ConsistencyReport()
    demonstrated_strengths: List[str] = []
    profile_strengths: List[str] = []
    development_gaps: List[str] = []
    unassessed_areas: List[str] = []
    recommendations: List[str] = []
    future_interview_focus: List[str] = []
