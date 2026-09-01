from pydantic import BaseModel, Field
from typing import List, Optional

class LinkedInAnalyzeRequest(BaseModel):
    profile_url: str = Field(..., description="Public LinkedIn profile URL, e.g. https://www.linkedin.com/in/username")

class LinkedInExperienceEntry(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

class LinkedInProfileData(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    experiences: List[LinkedInExperienceEntry] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class LinkedInAnalyzeResponse(BaseModel):
    profile_url: str
    linkedin_score: int = Field(75, ge=0, le=100)
    recruiter_visibility_score: int = Field(75, ge=0, le=100)
    headline_review: str = ""
    about_review: str = ""
    skills_analysis: List[str] = Field(default_factory=list)
    optimization_suggestions: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    improved_headline: str = ""
    improved_about: str = ""
    profile_data: Optional[LinkedInProfileData] = None

    # Sub-scores
    headline_score: int = Field(75, ge=0, le=100)
    banner_score: int = Field(75, ge=0, le=100)
    about_score: int = Field(75, ge=0, le=100)
    experience_score: int = Field(75, ge=0, le=100)
    skills_score: int = Field(75, ge=0, le=100)
    licenses_score: int = Field(75, ge=0, le=100)
    featured_score: int = Field(75, ge=0, le=100)
    recommendations_score: int = Field(75, ge=0, le=100)
    keyword_density_score: int = Field(75, ge=0, le=100)
    searchability_score: int = Field(75, ge=0, le=100)
