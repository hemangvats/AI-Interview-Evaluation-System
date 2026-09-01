from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from typing import Optional

from resumes.parser import parse_resume_file
from resumes.service import ResumeService
from resumes.schemas import ResumeAnalysisResponse, ResumeExtractedData, ATSAuditResult
from auth.deps import get_optional_current_user

resume_router = APIRouter(prefix="/api/v1/resumes", tags=["Resumes"])
resume_service = ResumeService()

@resume_router.post("/parse", response_model=ResumeExtractedData)
async def parse_resume_endpoint(
    file: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Parse an uploaded resume file (PDF, DOCX, TXT) and return structured extracted entities.
    """
    filename = file.filename or "resume.pdf"
    content = await file.read()
    
    try:
        raw_text = parse_resume_file(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    extracted = await resume_service.extract_structured_data(raw_text)
    return extracted

@resume_router.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume_endpoint(
    target_role: str = Form(""),
    file: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Upload resume file and get comprehensive structured extraction + ATS quality score audit.
    """
    filename = file.filename or "resume.pdf"
    content = await file.read()
    
    try:
        raw_text = parse_resume_file(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    result = await resume_service.process_resume(raw_text, target_role=target_role)
    result.file_name = filename
    return result
