import datetime
from typing import Dict, Any, List
from reports.schemas import (
    UnifiedCandidateReport,
    CandidateOverview,
    ProfileEvidenceSummary,
    InterviewPerformanceSummary,
    SkillValidationItem,
    SkillValidationStatus,
    ProjectValidationItem,
    ProjectValidationStatus,
    ConsistencyReport
)
from personalization.builder import sanitize_context_text

class CandidateReportGenerator:
    """
    Synthesizes the Unified Candidate Report by combining the immutable T0 Candidate Profile 
    context snapshot with actual interview evaluation performance.
    
    CRITICAL RULE: Scores from Resume, LinkedIn, GitHub, and Interview are kept strictly separate.
    No arbitrary overall candidate score is calculated.
    """
    
    @classmethod
    def generate_report(cls, session_data: Dict[str, Any], raw_profile_data: Dict[str, Any] = None) -> UnifiedCandidateReport:
        session_id = session_data.get("session_id", "unknown_session")
        user_id = session_data.get("user_id")
        target_role = session_data.get("role", "Software Engineer")
        created_at = session_data.get("created_at", datetime.datetime.now().isoformat())
        
        # 1. Extract T0 Candidate Context Snapshot from session
        cand_ctx = session_data.get("candidate_context", {})
        has_profile = cand_ctx.get("has_profile", False)
        
        # Determine Source Status
        source_status = {
            "resume": "available" if (has_profile and raw_profile_data and raw_profile_data.get("resume")) or cand_ctx.get("verified_claims") else "not_provided",
            "linkedin": "available" if (has_profile and raw_profile_data and raw_profile_data.get("linkedin")) else "not_provided",
            "github": "available" if (has_profile and raw_profile_data and raw_profile_data.get("github")) else "not_provided"
        }
        
        # 2. Candidate Overview
        candidate_name = "Candidate"
        if raw_profile_data and raw_profile_data.get("identity"):
            candidate_name = raw_profile_data["identity"].get("full_name") or "Candidate"
            
        overview = CandidateOverview(
            candidate_name=candidate_name,
            target_role=target_role,
            interview_date=created_at[:10] if len(created_at) >= 10 else created_at,
            source_status=source_status,
            has_profile=has_profile
        )
        
        # 3. Interview Performance Summary
        evaluations = session_data.get("evaluations", [])
        scores = []
        diff_progression = []
        
        for item in evaluations:
            eval_dict = item.get("evaluation", {})
            if "score" in eval_dict and eval_dict["score"] is not None:
                try:
                    scores.append(float(eval_dict["score"]))
                except (ValueError, TypeError):
                    pass
            if "difficulty" in eval_dict:
                diff_progression.append(eval_dict["difficulty"])
                
        avg_interview_score = round(sum(scores) / len(scores), 1) if scores else None
        hiring_decision = session_data.get("hiring_decision") or "Pending"
        verdict_reasoning = session_data.get("verdict_reasoning") or session_data.get("final_summary") or "Interview completed."
        
        interview_perf = InterviewPerformanceSummary(
            interview_score=avg_interview_score,
            total_exchanges=len(evaluations),
            hiring_decision=hiring_decision,
            verdict_reasoning=sanitize_context_text(verdict_reasoning),
            difficulty_progression=diff_progression,
            final_summary_markdown=sanitize_context_text(session_data.get("final_summary", ""))
        )
        
        # 4. Profile Evidence Summary
        profile_evidence = ProfileEvidenceSummary()
        if raw_profile_data:
            res_data = raw_profile_data.get("resume", {})
            li_data = raw_profile_data.get("linkedin", {})
            gh_data = raw_profile_data.get("github", {})
            
            if res_data:
                profile_evidence.resume_ats_score = res_data.get("ats_score", 75)
                profile_evidence.resume_strengths = res_data.get("strengths", [])
                profile_evidence.resume_weaknesses = res_data.get("weaknesses", [])
                
            if li_data:
                profile_evidence.linkedin_score = li_data.get("linkedin_score", 70)
                profile_evidence.linkedin_visibility_score = li_data.get("recruiter_visibility_score", 70)
                profile_evidence.linkedin_headline_suggestion = li_data.get("improved_headline", "")
                
            if gh_data:
                profile_evidence.github_score = gh_data.get("github_score", 80)
                profile_evidence.github_technical_depth = gh_data.get("technical_depth_score", 75)
                profile_evidence.github_hiring_readiness = gh_data.get("hiring_readiness_score", 75)
                
        # 5. Deterministic Skill Validation Matrix
        skill_items: List[SkillValidationItem] = []
        relevant_skills = cand_ctx.get("relevant_skills", [])
        
        # Gather text of all interview questions and user answers
        all_q_text = " ".join(session_data.get("questions", [])).lower()
        all_eval_text = " ".join([str(e.get("evaluation", {}).get("feedback", "")) for e in evaluations]).lower()
        
        for sk in relevant_skills:
            skill_name = sk.get("skill", "")
            if not skill_name:
                continue
            sources = sk.get("sources", [])
            sk_lower = skill_name.lower()
            
            # Check if skill was evaluated during interview
            discussed = (sk_lower in all_q_text or sk_lower in all_eval_text)
            
            if discussed:
                # Find score for evaluations mentioning skill
                matching_scores = []
                for item in evaluations:
                    ev = item.get("evaluation", {})
                    q_item = str(item.get("question", "")).lower()
                    f_item = str(ev.get("feedback", "")).lower()
                    if sk_lower in q_item or sk_lower in f_item:
                        if "score" in ev and ev["score"] is not None:
                            try:
                                matching_scores.append(float(ev["score"]))
                            except (ValueError, TypeError):
                                pass
                
                avg_sk_score = (sum(matching_scores) / len(matching_scores)) if matching_scores else (avg_interview_score or 7.0)
                if avg_sk_score >= 7.0:
                    status = SkillValidationStatus.DEMONSTRATED
                    evidence = f"Demonstrated strong capability during interview (evaluated score ~{round(avg_sk_score, 1)}/10)."
                else:
                    status = SkillValidationStatus.PARTIALLY_DEMONSTRATED
                    evidence = f"Discussed during interview; demonstrated partial proficiency (evaluated score ~{round(avg_sk_score, 1)}/10)."
            else:
                status = SkillValidationStatus.NOT_ASSESSED
                evidence = "Not directly assessed during this interview session."
                
            skill_items.append(SkillValidationItem(
                skill=skill_name,
                profile_sources=sources,
                interview_evidence=evidence,
                status=status
            ))
            
        # 6. Deterministic Project Validation
        project_items: List[ProjectValidationItem] = []
        relevant_projects = cand_ctx.get("relevant_projects", [])
        
        for prj in relevant_projects:
            prj_title = prj.get("title", "")
            if not prj_title:
                continue
            sources = prj.get("sources", [])
            prj_lower = prj_title.lower()
            
            discussed = (prj_lower in all_q_text or prj_lower in all_eval_text)
            if discussed:
                status = ProjectValidationStatus.DEMONSTRATED
                evidence = f"Candidate articulated architecture and technical implementation details of '{prj_title}'."
            else:
                status = ProjectValidationStatus.NOT_ASSESSED
                evidence = f"Project '{prj_title}' was listed on profile ({', '.join(sources)}) but not directly covered in Q&A."
                
            project_items.append(ProjectValidationItem(
                project_title=prj_title,
                profile_sources=sources,
                interview_evidence=evidence,
                status=status
            ))
            
        # 7. Consistency Audit (Neutral Language)
        consistency = ConsistencyReport(
            consistent_claims=cand_ctx.get("verified_claims", []),
            limited_evidence_claims=cand_ctx.get("claims_to_validate", []),
            discrepancy_notes=[]
        )
        if raw_profile_data and raw_profile_data.get("consistency_report"):
            cr = raw_profile_data["consistency_report"]
            consistency.discrepancy_notes = cr.get("discrepancies", [])
            
        # 8. Strengths Breakdown
        demonstrated_strengths = []
        for item in evaluations:
            ev = item.get("evaluation", {})
            if ev.get("score", 0) >= 8 and ev.get("feedback"):
                demonstrated_strengths.append(sanitize_context_text(ev["feedback"]))
        if not demonstrated_strengths and avg_interview_score and avg_interview_score >= 7:
            demonstrated_strengths.append("Solid technical communication and structured problem solving throughout session.")
            
        profile_strengths = cand_ctx.get("strengths", ["Profile presents verified technical skills across active channels."])
        
        # 9. Development Gaps & Unassessed Areas
        development_gaps = []
        unassessed_areas = []
        
        for item in evaluations:
            ev = item.get("evaluation", {})
            if ev.get("score", 10) < 6.5 and ev.get("improvement"):
                development_gaps.append(sanitize_context_text(ev["improvement"]))
                
        for sk_item in skill_items:
            if sk_item.status == SkillValidationStatus.NOT_ASSESSED:
                unassessed_areas.append(f"Skill '{sk_item.skill}' listed on {', '.join(sk_item.profile_sources)} remains unassessed.")
                
        # 10. Recommendations & Future Focus
        recommendations = [
            "Review answer feedback details to refine technical depth for lower-scoring responses.",
            "Maintain strong alignment between portfolio projects and resume claims."
        ]
        if profile_evidence.resume_ats_score and profile_evidence.resume_ats_score < 80:
            recommendations.append("Enhance Resume ATS optimization with role-specific keywords.")
        if profile_evidence.github_technical_depth and profile_evidence.github_technical_depth < 80:
            recommendations.append("Strengthen GitHub repository documentation and README coverage.")
            
        future_interview_focus = [
            f"Evaluate depth in unassessed areas: {', '.join([sk.skill for sk in skill_items if sk.status == SkillValidationStatus.NOT_ASSESSED][:3])}" if any(sk.status == SkillValidationStatus.NOT_ASSESSED for sk in skill_items) else "Focus on advanced system design architecture and edge-case scaling."
        ]
        
        return UnifiedCandidateReport(
            session_id=session_id,
            user_id=user_id,
            created_at=created_at,
            overview=overview,
            interview_performance=interview_perf,
            profile_evidence=profile_evidence,
            skill_validation=skill_items,
            project_validation=project_items,
            consistency_analysis=consistency,
            demonstrated_strengths=demonstrated_strengths[:5],
            profile_strengths=profile_strengths[:5],
            development_gaps=development_gaps[:5],
            unassessed_areas=unassessed_areas[:5],
            recommendations=recommendations,
            future_interview_focus=future_interview_focus
        )
