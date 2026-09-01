from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class EducationEntry(BaseModel):
    school: str = Field(..., description="Name of the university, college, or school")
    degree: str = Field(..., description="Degree obtained, e.g. B.S., M.S., Ph.D., Diploma")
    field_of_study: Optional[str] = Field(None, description="Field of study, major, or specialization")
    start_date: Optional[str] = Field(None, description="Start date (e.g. '2018-09')")
    end_date: Optional[str] = Field(None, description="End date (e.g. '2022-06' or 'Present')")

class ExperienceEntry(BaseModel):
    company: str = Field(..., description="Company or organization name")
    role: str = Field(..., description="Job title or designation")
    location: Optional[str] = Field(None, description="Job location")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    description: Optional[str] = Field(None, description="Bullet points of responsibilities and achievements")

class ProjectEntry(BaseModel):
    title: str = Field(..., description="Title of the project")
    description: str = Field(..., description="Detailed project description")
    technologies: List[str] = Field(default_factory=list, description="Technologies and frameworks used")

class ResumeExtractedData(BaseModel):
    name: str = Field("Candidate", description="Full name of candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills")
    education: List[EducationEntry] = Field(default_factory=list, description="Education history")
    experience: List[ExperienceEntry] = Field(default_factory=list, description="Work experience history")
    projects: List[ProjectEntry] = Field(default_factory=list, description="Key projects")
    certifications: List[str] = Field(default_factory=list, description="Certifications and credentials")

class ATSAuditResult(BaseModel):
    formatting_score: int = Field(80, ge=0, le=100)
    keyword_score: int = Field(80, ge=0, le=100)
    skills_score: int = Field(80, ge=0, le=100)
    experience_score: int = Field(80, ge=0, le=100)
    education_score: int = Field(80, ge=0, le=100)
    project_score: int = Field(80, ge=0, le=100)
    final_ats_score: int = Field(80, ge=0, le=100)
    missing_sections: List[str] = Field(default_factory=list)
    weak_bullet_points: List[str] = Field(default_factory=list)
    suggested_keywords: List[str] = Field(default_factory=list)

class ResumeAnalysisResponse(BaseModel):
    file_name: str
    raw_text: str
    extracted_data: ResumeExtractedData
    ats_audit: ATSAuditResult
    normalized_context: str
