from pydantic import BaseModel, Field
from typing import List, Optional

class GitHubAnalyzeRequest(BaseModel):
    username: str = Field(..., description="GitHub username or profile URL, e.g. octocat or https://github.com/octocat")

class GitHubRepoData(BaseModel):
    name: str
    stargazers_count: int = 0
    forks_count: int = 0
    language: Optional[str] = None
    commits_count: Optional[int] = 10
    readme: Optional[str] = None

class GitHubProfileData(BaseModel):
    name: Optional[str] = None
    login: str
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    avatar_url: Optional[str] = None

class GitHubFullData(BaseModel):
    profile: GitHubProfileData
    repositories: List[GitHubRepoData] = Field(default_factory=list)

class GitHubAnalyzeResponse(BaseModel):
    username: str
    github_score: int = Field(75, ge=0, le=100)
    technical_depth_score: int = Field(70, ge=0, le=100)
    hiring_readiness_score: int = Field(70, ge=0, le=100)
    project_quality_score: int = Field(75, ge=0, le=100)
    languages_extracted: List[str] = Field(default_factory=list)
    readme_evaluations: str = ""
    missing_project_recommendations: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    github_data: Optional[GitHubFullData] = None

    # Sub-scores
    repositories_score: int = Field(70, ge=0, le=100)
    documentation_score: int = Field(70, ge=0, le=100)
    testing_score: int = Field(70, ge=0, le=100)
    architecture_score: int = Field(70, ge=0, le=100)
    consistency_score: int = Field(70, ge=0, le=100)

    # Repository audits
    best_documented_repo: Optional[str] = "N/A"
    most_active_repo: Optional[str] = "N/A"
    largest_project: Optional[str] = "N/A"
    highest_complexity_project: Optional[str] = "N/A"
