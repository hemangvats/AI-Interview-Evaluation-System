from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RelevantSkill(BaseModel):
    skill: str
    sources: List[str] = Field(default_factory=list)
    is_multi_source: bool = False

class RelevantProject(BaseModel):
    title: str
    description: str = ""
    sources: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)

class RelevantExperience(BaseModel):
    role: str
    company: str
    dates: str = "N/A"
    sources: List[str] = Field(default_factory=list)

class InterviewCandidateContext(BaseModel):
    target_role: str
    has_profile: bool = False
    relevant_skills: List[RelevantSkill] = Field(default_factory=list)
    relevant_projects: List[RelevantProject] = Field(default_factory=list)
    relevant_experience: List[RelevantExperience] = Field(default_factory=list)
    verified_claims: List[str] = Field(default_factory=list)
    claims_to_validate: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    suggested_initial_difficulty: str = "Intermediate"
    context_summary: str = ""
