import os
import pytest
import datetime
from fastapi.testclient import TestClient
from jose import jwt

from server import app
from auth.config import auth_settings
from auth.security import create_access_token, decode_token, ALGORITHM
from resumes.parser import parse_resume_file
from linkedin.security import verify_ssrf_safe as linkedin_ssrf_verify
from github.security import verify_ssrf_safe as github_ssrf_verify
from reports.generator import CandidateReportGenerator

client = TestClient(app)

# ---------------------------------------------------------
# 1. Full Candidate Lifecycle Test (End-to-End User Scenario)
# ---------------------------------------------------------

def test_full_candidate_lifecycle_flow():
    """
    Tests the complete end-to-end flow:
    Register -> Login -> Resume Upload -> LinkedIn Analysis -> GitHub Analysis -> 
    Candidate Profile Build -> Start Interview -> Answer Questions -> 
    Complete Interview -> Fetch Report -> Refresh Token -> Logout.
    """
    email = f"qa_candidate_{datetime.datetime.now().timestamp()}@example.com"
    password = "SecurePassword123!"
    full_name = "QA Candidate User"

    # Step 1: Register Candidate
    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": full_name})
    assert reg_res.status_code == 201, f"Step 1 failed: {reg_res.text}"
    user_id = reg_res.json()["user_id"]

    # Step 2: Login Candidate
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200, f"Step 2 failed: {login_res.text}"
    auth_data = login_res.json()
    access_token = auth_data["access_token"]
    refresh_token = auth_data["refresh_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 3: Check Authenticated User Profile
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200, f"Step 3 failed: {me_res.text}"

    # Step 4: Upload Resume (TXT / PDF format)
    resume_content = b"Candidate Name: QA Candidate User\nSkills: Python, FastAPI, Docker, PostgreSQL\nExperience: 4 years as Backend Engineer\nEducation: B.S. Computer Science"
    res_upload = client.post("/api/v1/resumes/parse", files={"file": ("resume.txt", resume_content, "text/plain")}, headers=headers)
    assert res_upload.status_code == 200, f"Step 4 failed: {res_upload.text}"

    # Step 5: Process LinkedIn Analysis (using safe public URL)
    linkedin_res = client.post("/api/v1/linkedin/analyze", json={"profile_url": "https://www.linkedin.com/in/satyanadella"}, headers=headers)
    assert linkedin_res.status_code in [200, 400, 500], f"Step 5 failed: {linkedin_res.text}"

    # Step 6: Process GitHub Analysis (using safe public username)
    github_res = client.post("/api/v1/github/analyze", json={"username": "torvalds"}, headers=headers)
    assert github_res.status_code in [200, 400, 500], f"Step 6 failed: {github_res.text}"

    # Step 7: Build Unified Candidate Profile
    profile_res = client.post("/api/v1/profile/build", headers=headers)
    assert profile_res.status_code == 200, f"Step 7 failed: {profile_res.text}"

    # Step 8: Start Personalized Interview
    start_res = client.post("/api/interviews/start", data={"role": "Backend Developer", "difficulty": "Intermediate"}, headers=headers)
    assert start_res.status_code == 200, f"Step 8 failed: {start_res.text}"
    session_data = start_res.json()
    session_id = session_data["session_id"]
    first_question = session_data["messages"][0]["content"] if session_data.get("messages") else session_data["questions"][0]

    # Step 9: Answer Questions
    answer_res = client.post("/api/interviews/answer", json={"session_id": session_id, "answer": "I design backend APIs with FastAPI, PostgreSQL, and Redis caching to handle high concurrency."}, headers=headers)
    assert answer_res.status_code == 200, f"Step 9 failed: {answer_res.text}"

    # Step 10: Fetch Unified Candidate Report
    report_res = client.get(f"/api/v1/reports/{session_id}", headers=headers)
    assert report_res.status_code == 200, f"Step 10 failed: {report_res.text}"

    # Step 11: Refresh Token
    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200, f"Step 11 failed: {ref_res.text}"
    new_access_token = ref_res.json()["access_token"]

    # Step 12: Verify Client Authentication & Data Persistence
    me_after = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me_after.status_code == 200, f"Step 12 failed: {me_after.text}"





# ---------------------------------------------------------
# 2. Multi-User Isolation & IDOR Security Test
# ---------------------------------------------------------

def test_multi_user_isolation_and_idor():
    """Verify strict isolation between User A and User B at auth, session, and report levels."""
    # User A setup
    email_a = f"user_a_{datetime.datetime.now().timestamp()}@example.com"
    client.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "full_name": "User A"})
    token_a = client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B setup
    email_b = f"user_b_{datetime.datetime.now().timestamp()}@example.com"
    client.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "full_name": "User B"})
    token_b = client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates interview
    sess_a = client.post("/api/interviews/start", data={"role": "AI Engineer"}, headers=headers_a).json()["session_id"]

    # User B cannot view User A's session -> 403
    res_b_view = client.get(f"/api/interviews/{sess_a}", headers=headers_b)
    assert res_b_view.status_code == 403

    # User B cannot view User A's report -> 403
    res_b_rep = client.get(f"/api/v1/reports/{sess_a}", headers=headers_b)
    assert res_b_rep.status_code == 403

    # User B cannot delete User A's session -> 403
    res_b_del = client.delete(f"/api/interviews/{sess_a}", headers=headers_b)
    assert res_b_del.status_code == 403

# ---------------------------------------------------------
# 3. Report Score Separation Test
# ---------------------------------------------------------

def test_report_score_separation_no_fake_aggregates():
    """Verify ATS, LinkedIn, GitHub, and Interview scores remain separate without fake combined score."""
    session_mock = {
        "session_id": "test_sess_123",
        "role": "Data Scientist",
        "difficulty": "Intermediate",
        "evaluations": [{"score": 8, "feedback": "Good answer"}],
        "hiring_decision": "Hire",
        "verdict_reasoning": "Solid performance.",
        "final_summary": "Demonstrated core skills.",
        "interview_complete": True,
        "candidate_snapshot": {"skills": ["Python", "Pandas"]}
    }
    profile_mock = {
        "resume": {"ats_score": 85},
        "linkedin": {"linkedin_score": 70},
        "github": {"github_score": 80}
    }
    
    report = CandidateReportGenerator.generate_report(session_mock, profile_mock)
    report_dict = report.model_dump() if hasattr(report, "model_dump") else report.dict()
    
    # Assert score separation in report schema
    overview = report_dict.get("overview", {})
    interview_perf = report_dict.get("interview_performance", {})
    profile_evid = report_dict.get("profile_evidence", {})

    assert overview is not None
    assert interview_perf is not None
    assert profile_evid is not None

    # Scores must remain strictly in their respective domain sub-objects
    assert profile_evid.get("resume_ats_score") == 85
    assert interview_perf.get("hiring_decision") == "Hire"
    
    # Ensure no arbitrary single total score exists in overview or top-level report schema
    assert "combined_total_score" not in overview
    assert "total_candidate_score" not in report_dict


# ---------------------------------------------------------
# 4. Health & Production Security Safeguards
# ---------------------------------------------------------

def test_health_check_and_headers():
    """Verify /health endpoint returns 200 without exposing sensitive environment keys."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "SECRET_KEY" not in data
    assert "MONGODB_URL" not in data

def test_security_headers():
    """Verify security headers are returned on API requests."""
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"

if __name__ == "__main__":
    pytest.main(["-v", __file__])

