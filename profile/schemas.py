from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SourceStatusMap(BaseModel):
    resume: str = "not_provided"     # not_provided | processing | available | failed | stale
    linkedin: str = "not_provided"
    github: str = "not_provided"

class SourceTimestamps(BaseModel):
    resume_updated_at: Optional[str] = None
    linkedin_updated_at: Optional[str] = None
    github_updated_at: Optional[str] = None

class SkillEvidence(BaseModel):
    skill: str
    sources: List[str] = Field(default_factory=list)

class NormalizedExperience(BaseModel):
    role: str
    company: str
    dates: Optional[str] = "N/A"
    description: Optional[str] = ""
    sources: List[str] = Field(default_factory=list)

class NormalizedEducation(BaseModel):
    degree: str
    institution: str
    dates: Optional[str] = "N/A"
    sources: List[str] = Field(default_factory=list)

class NormalizedProject(BaseModel):
    title: str
    description: Optional[str] = ""
    technologies: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

class CrossSourceConsistency(BaseModel):
    consistency_score: int = Field(80, ge=0, le=100)
    consistent_claims: List[str] = Field(default_factory=list)
    potential_discrepancies: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)

class UnifiedCandidateProfile(BaseModel):
    user_id: str
    identity: Dict[str, Any] = Field(default_factory=dict)
    
    # Source specific data payloads
    resume: Optional[Dict[str, Any]] = None
    linkedin: Optional[Dict[str, Any]] = None
    github: Optional[Dict[str, Any]] = None
    
    # Normalized candidate data
    unified_skills: List[SkillEvidence] = Field(default_factory=list)
    unified_experience: List[NormalizedExperience] = Field(default_factory=list)
    unified_education: List[NormalizedEducation] = Field(default_factory=list)
    unified_projects: List[NormalizedProject] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    
    # Cross-source intelligence & insights
    consistency_report: CrossSourceConsistency = Field(default_factory=CrossSourceConsistency)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Status & metadata
    source_status: SourceStatusMap = Field(default_factory=SourceStatusMap)
    timestamps: SourceTimestamps = Field(default_factory=SourceTimestamps)
    created_at: str = ""
    updated_at: str = ""

class ProfileBuildRequest(BaseModel):
    resume_id: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
