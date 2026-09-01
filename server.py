import io
import datetime
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import PyPDF2

from llm_helper import InterviewManager
from database_helper import DatabaseManager
from auth.database import connect_to_mongo, close_mongo_connection
from auth.router import auth_router
from auth.deps import get_optional_current_user
from resumes.router import resume_router
from resumes.parser import parse_resume_file
from resumes.service import ResumeService
from linkedin.router import linkedin_router
from github.router import github_router
from profile.router import profile_router
from profile.service import candidate_profile_service
from personalization.builder import context_builder

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time

app = FastAPI(title="AI Interview Bot API", lifespan=lifespan)

# CORS Security Configuration
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security Headers & Rate-Limiting Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_counts: Dict[str, List[float]] = {}
        self.rate_limit_max = 60  # max requests
        self.rate_limit_window = 60.0  # window in seconds

    async def dispatch(self, request: Request, call_next):
        # Sliding window rate limiting for sensitive API routes
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        if request.url.path.startswith("/api/v1/auth/") or request.url.path.startswith("/api/interviews/start"):
            timestamps = self.request_counts.get(client_ip, [])
            timestamps = [ts for ts in timestamps if now - ts < self.rate_limit_window]
            if len(timestamps) >= self.rate_limit_max:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Rate limit exceeded. Please wait before retrying."}
                )
            timestamps.append(now)
            self.request_counts[client_ip] = timestamps

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Global Exception Handler preventing stack trace leak
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    print(f"Unhandled Exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Saathi AI Interview Coach",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(linkedin_router)
app.include_router(github_router)
app.include_router(profile_router)

db_manager = DatabaseManager()
resume_service = ResumeService()

try:
    interview_manager = InterviewManager()
except Exception as e:
    print(f"Error initializing Ollama: {e}. Please ensure Ollama is running.")
    interview_manager = None


# Fallback in-memory storage for sessions if Supabase is not connected
LOCAL_SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if db_manager.is_connected():
        session = db_manager.get_interview_by_id(session_id, user_id=user_id)
        if session:
            return session
    session = LOCAL_SESSIONS.get(session_id)
    if session:
        if user_id is not None and session.get("user_id") != user_id:
            return None
        return session
    return None

def save_session(session_id: str, data: Dict[str, Any]) -> bool:
    if db_manager.is_connected():
        db_manager.save_interview(data)
    LOCAL_SESSIONS[session_id] = data
    return True

def delete_session(session_id: str, user_id: Optional[str] = None) -> bool:
    if db_manager.is_connected():
        db_manager.delete_interview(session_id, user_id=user_id)
    if session_id in LOCAL_SESSIONS:
        sess = LOCAL_SESSIONS[session_id]
        if user_id is not None and sess.get("user_id") != user_id:
            return False
        del LOCAL_SESSIONS[session_id]
        return True
    return False

def list_sessions(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if db_manager.is_connected():
        sessions = db_manager.get_all_interviews(user_id=user_id)
        if sessions is not None and len(sessions) > 0:
            return sessions
    
    # Return brief info from local sessions
    result = []
    for sid, data in LOCAL_SESSIONS.items():
        sess_user_id = data.get("user_id")
        if user_id is not None and sess_user_id != user_id:
            continue
        result.append({
            "session_id": sid,
            "role": data.get("role"),
            "difficulty": data.get("difficulty"),
            "interview_complete": data.get("interview_complete"),
            "created_at": sid,
            "user_id": sess_user_id
        })
    result.sort(key=lambda x: x["session_id"], reverse=True)
    return result

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

@app.get("/api/config")
async def get_config():
    return {
        "db_connected": db_manager.is_connected(),
        "roles": [
            "AI Engineer", 
            "Software Developer", 
            "Data Scientist", 
            "Web Developer", 
            "Frontend Developer", 
            "Backend Developer"
        ]
    }

@app.get("/api/interviews")
async def get_interviews(
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    user_id = current_user["_id"] if current_user else None
    return list_sessions(user_id=user_id)

@app.get("/api/interviews/{session_id}")
async def get_interview_detail(
    session_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    user_id = current_user["_id"] if current_user else None
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
        
    session_owner = session.get("user_id")
    if current_user:
        if session_owner and session_owner != user_id:
            raise HTTPException(status_code=403, detail="Access denied: You do not own this interview session.")
    elif session_owner:
        raise HTTPException(status_code=403, detail="Access denied: Authentication required for this interview session.")
        
    return session

@app.delete("/api/interviews/{session_id}")
async def delete_interview_detail(
    session_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    user_id = current_user["_id"] if current_user else None
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
        
    session_owner = session.get("user_id")
    if current_user:
        if session_owner and session_owner != user_id:
            raise HTTPException(status_code=403, detail="Access denied: You do not own this interview session.")
    elif session_owner:
        raise HTTPException(status_code=403, detail="Access denied: Authentication required.")
        
    success = delete_session(session_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete session.")
    return {"status": "success", "message": "Interview deleted successfully."}

@app.post("/api/interviews/start")
async def start_interview(
    role: str = Form(...),
    resume: Optional[UploadFile] = File(None),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    if not interview_manager:
        raise HTTPException(
            status_code=503, 
            detail="AI model manager not initialized. Please ensure Ollama is running and has model 'llama3.2:3b'."
        )
    
    user_id = current_user["_id"] if current_user else None
    resume_text = ""
    resume_structured = None
    ats_audit = None
    
    if resume is not None and resume.filename:
        filename = resume.filename
        content = await resume.read()
        if content:
            try:
                raw_text = parse_resume_file(content, filename)
                res_analysis = await resume_service.process_resume(raw_text, target_role=role)
                resume_text = res_analysis.normalized_context or raw_text
                resume_structured = res_analysis.extracted_data.model_dump()
                ats_audit = res_analysis.ats_audit.model_dump()
                if user_id:
                    await candidate_profile_service.refresh_source(user_id, "resume", res_analysis.model_dump())
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            except Exception as e:
                print(f"Error processing resume: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to parse resume: {str(e)}")

    # Fetch Unified Candidate Profile if authenticated
    candidate_profile = None
    if user_id:
        try:
            candidate_profile = await candidate_profile_service.get_or_create_profile(user_id, user_info=current_user)
        except Exception as e:
            print(f"Notice: Could not load candidate profile for user {user_id}: {e}")

    # Build Candidate Context Snapshot (T0)
    cand_context = context_builder.build_interview_context(role, candidate_profile)
    cand_context_dict = cand_context.model_dump()
    cand_context_summary = cand_context.context_summary

    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize session with immutable Candidate Context snapshot (T0)
    intro_note = " *(Personalized from your candidate profile)*" if cand_context.has_profile else ""
    session_data = {
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "difficulty": cand_context.suggested_initial_difficulty if cand_context.has_profile else "Adaptive",
        "messages": [{
            "role": "assistant",
            "content": f"Hello! I am Saathi, your AI Interview Coach.{intro_note} I'll be evaluating your fit for the **{role}** position.\n\nPlease introduce yourself and walk me through your relevant experience for this role."
        }],
        "questions": ["Introduction and Candidate Walkthrough"],
        "current_q_index": 0,
        "evaluations": [],
        "interview_complete": False,
        "final_summary": "",
        "total_questions": 15,
        "hiring_decision": None,
        "verdict_reasoning": "",
        "resume_text": resume_text,
        "resume_structured": resume_structured,
        "ats_audit": ats_audit,
        "candidate_context": cand_context_dict,
        "candidate_context_summary": cand_context_summary,
        "interview_phase": "intro"
    }
    
    save_session(session_id, session_data)
    return session_data

@app.post("/api/interviews/answer")
async def submit_answer(
    req: AnswerRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    if not interview_manager:
        raise HTTPException(status_code=503, detail="AI model manager not initialized.")
    
    user_id = current_user["_id"] if current_user else None
    session_id = req.session_id
    prompt = req.answer.strip()
    
    # Load session
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
        
    session_owner = session.get("user_id")
    if current_user:
        if session_owner and session_owner != user_id:
            raise HTTPException(status_code=403, detail="Access denied: You do not own this interview session.")
    elif session_owner:
        raise HTTPException(status_code=403, detail="Access denied: Authentication required for this interview session.")
        
    if session.get("interview_complete"):
        raise HTTPException(status_code=400, detail="Interview is already completed.")
        
    messages = session.get("messages", [])
    questions = session.get("questions", [])
    current_q_index = session.get("current_q_index", 0)
    evaluations = session.get("evaluations", [])
    selected_role = session.get("role", "")
    selected_difficulty = session.get("difficulty", "Adaptive")
    resume_text = session.get("resume_text", "")
    total_questions = session.get("total_questions", 15)
    interview_phase = session.get("interview_phase", "technical")
    candidate_context_summary = session.get("candidate_context_summary", "")
    
    # Add user message to history
    messages.append({"role": "user", "content": prompt})
    
    current_question = questions[current_q_index]
    
    # Evaluate answer with Candidate Context Snapshot (T0)
    evaluation = interview_manager.evaluate_answer(
        selected_role, current_question, prompt, 
        selected_difficulty, resume_text,
        current_q_index + 1,
        candidate_context_summary=candidate_context_summary
    )
    
    evaluations.append({
        "question": current_question,
        "answer": prompt,
        "evaluation": evaluation
    })
    
    score = evaluation.get("score", 0)
    
    feedback_msg = f"**Previous Reply Feedback**:\n"
    feedback_msg += f"- **Score**: {score}/10\n"
    feedback_msg += f"- **Feedback**: {evaluation.get('feedback', '')}\n"
    feedback_msg += f"- **Improvement**: {evaluation.get('suggestions', '')}\n"
    
    # Adjust difficulty
    diff_levels = ["Beginner", "Intermediate", "Advanced", "Adaptive"]
    try:
        curr_idx = diff_levels.index(selected_difficulty)
    except ValueError:
        curr_idx = 1 # Default to Intermediate
        
    adj = evaluation.get("difficulty_adjustment", "stay")
    if adj == "increase" and curr_idx < 2 and score >= 6:
        selected_difficulty = diff_levels[curr_idx + 1]
        feedback_msg += f"\n📈 *Great job! Increasing difficulty to **{selected_difficulty}** for the next question.*\n"
    elif adj == "decrease" and curr_idx > 0 and score < 5:
        selected_difficulty = diff_levels[curr_idx - 1]
        feedback_msg += f"\n📉 *Adjusting difficulty to **{selected_difficulty}** to help you build confidence.*\n"
        
    feedback_msg += "\n---\n"
    current_q_index += 1
    
    # Update phase
    if current_q_index == 1:
        interview_phase = "technical"
        
    # Check completion
    min_questions = 4
    llm_wants_to_end = evaluation.get("is_interview_complete", False)
    
    hiring_decision = session.get("hiring_decision")
    verdict_reasoning = session.get("verdict_reasoning", "")
    final_summary = session.get("final_summary", "")
    interview_complete = False
    
    if (llm_wants_to_end and current_q_index >= min_questions) or current_q_index >= total_questions:
        feedback_msg += "\n🎉 **Interview Complete!** I have gathered enough information for a final verdict. See below."
        interview_complete = True
        
        # Capture verdict from the last evaluation
        hiring_decision = evaluation.get("hiring_decision", "")
        verdict_reasoning = evaluation.get("verdict_reasoning", "")
        
        if not hiring_decision:
            # Fallback evaluation
            summary_data = interview_manager.evaluate_answer(
                selected_role, "Final Review", "System concluding interview.",
                selected_difficulty, resume_text,
                current_q_index,
                candidate_context_summary=candidate_context_summary
            )
            hiring_decision = summary_data.get("hiring_decision", "Decision Pending")
            verdict_reasoning = summary_data.get("verdict_reasoning", "The candidate reached the maximum number of questions.")
            
        # Generate final summary report
        final_summary = interview_manager.generate_final_summary(selected_role, evaluations)
    else:
        follow_up = evaluation.get("follow_up_question", "")
        if follow_up and interview_phase == "technical":
            next_q = follow_up
            feedback_msg += f"🔍 *Follow-up Question:*\n"
        else:
            is_closing = current_q_index >= 7
            next_q_list = interview_manager.generate_questions(
                selected_role, 1, selected_difficulty,
                resume_text, questions, is_behavioral=is_closing,
                candidate_context_summary=candidate_context_summary
            )
            next_q = next_q_list[0] if next_q_list else "Tell me more about your experience."
            
        questions.append(next_q)
        feedback_msg += f"**Question {current_q_index + 1}:** {next_q}"
        
    # Append feedback message to history
    messages.append({"role": "assistant", "content": feedback_msg})
    
    # Save back to session
    session["messages"] = messages
    session["questions"] = questions
    session["current_q_index"] = current_q_index
    session["evaluations"] = evaluations
    session["difficulty"] = selected_difficulty
    session["interview_complete"] = interview_complete
    session["interview_phase"] = interview_phase
    session["hiring_decision"] = hiring_decision
    session["verdict_reasoning"] = verdict_reasoning
    session["final_summary"] = final_summary
    
    # Generate Unified Report if interview completed
    if interview_complete:
        from reports.generator import CandidateReportGenerator
        raw_profile = None
        if user_id:
            try:
                raw_profile = await candidate_profile_service.get_unified_profile(user_id)
            except Exception:
                pass
        report = CandidateReportGenerator.generate_report(session, raw_profile)
        session["unified_report"] = report.dict()
        
    save_session(session_id, session)
    return session

# ── UNIFIED CANDIDATE REPORT ENDPOINT ──
@app.get("/api/v1/reports/{session_id}")
async def get_unified_candidate_report(session_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
        
    session_owner = session.get("user_id")
    if session_owner:
        if not current_user or str(current_user["_id"]) != str(session_owner):
            raise HTTPException(status_code=403, detail="Access denied: You do not own this interview report.")
            
    if session.get("unified_report"):
        return session["unified_report"]
        
    from reports.generator import CandidateReportGenerator
    raw_profile = None
    if session_owner:
        try:
            raw_profile = await candidate_profile_service.get_unified_profile(session_owner)
        except Exception:
            pass
            
    report = CandidateReportGenerator.generate_report(session, raw_profile)
    return report.dict()

# Serve UI
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")
