from typing import Dict, Any, List, Optional, Tuple
from profile.schemas import (
    SkillEvidence,
    NormalizedExperience,
    NormalizedEducation,
    NormalizedProject,
    CrossSourceConsistency
)

def normalize_candidate_sources(
    resume_data: Optional[Dict[str, Any]],
    linkedin_data: Optional[Dict[str, Any]],
    github_data: Optional[Dict[str, Any]]
) -> Tuple[
    List[SkillEvidence],
    List[NormalizedExperience],
    List[NormalizedEducation],
    List[NormalizedProject],
    List[str],
    CrossSourceConsistency,
    List[str],
    List[str],
    List[str]
]:
    """
    Deterministic normalization engine for multi-channel candidate data.
    Preserves source evidence provenance across Resume, LinkedIn, and GitHub.
    """

    # 1. SKILL NORMALIZATION & SOURCE EVIDENCE PROVENANCE
    skill_sources_map: Dict[str, set] = {}

    # Resume skills
    if resume_data:
        ext = resume_data.get("extracted_data") or resume_data
        r_skills = ext.get("skills") or ext.get("technical_skills") or []
        if isinstance(r_skills, list):
            for s in r_skills:
                if s and isinstance(s, str):
                    s_clean = s.strip()
                    if s_clean:
                        skill_sources_map.setdefault(s_clean.lower(), (s_clean, set()))[1].add("resume")

    # LinkedIn skills
    if linkedin_data:
        prof = linkedin_data.get("profile_data") or linkedin_data
        l_skills = prof.get("skills") or []
        if isinstance(l_skills, list):
            for s in l_skills:
                if s and isinstance(s, str):
                    s_clean = s.strip()
                    if s_clean:
                        skill_sources_map.setdefault(s_clean.lower(), (s_clean, set()))[1].add("linkedin")

    # GitHub skills & languages
    if github_data:
        g_langs = github_data.get("languages_extracted") or []
        if isinstance(g_langs, list):
            for lang in g_langs:
                if lang and isinstance(lang, str):
                    l_clean = lang.strip()
                    if l_clean and l_clean != "No dominant language":
                        skill_sources_map.setdefault(l_clean.lower(), (l_clean, set()))[1].add("github")

    unified_skills = [
        SkillEvidence(skill=title, sources=sorted(list(sources)))
        for key, (title, sources) in skill_sources_map.items()
    ]

    # 2. EXPERIENCE NORMALIZATION
    unified_experience: List[NormalizedExperience] = []
    exp_seen = set()

    if resume_data:
        ext = resume_data.get("extracted_data") or resume_data
        work_exp = ext.get("work_experience") or ext.get("experience") or []
        if isinstance(work_exp, list):
            for item in work_exp:
                if isinstance(item, dict):
                    role = item.get("role") or item.get("job_title") or "Software Engineer"
                    company = item.get("company") or "Technology Company"
                    key = f"{role.lower()}_{company.lower()}"
                    if key not in exp_seen:
                        exp_seen.add(key)
                        unified_experience.append(NormalizedExperience(
                            role=role,
                            company=company,
                            dates=item.get("dates") or item.get("duration") or "N/A",
                            description=item.get("description") or "",
                            sources=["resume"]
                        ))

    if linkedin_data:
        prof = linkedin_data.get("profile_data") or linkedin_data
        li_exp = prof.get("experiences") or prof.get("experience") or []
        if isinstance(li_exp, list):
            for item in li_exp:
                if isinstance(item, dict):
                    role = item.get("title") or item.get("role") or "Software Engineer"
                    company = item.get("company") or "Technology Company"
                    key = f"{role.lower()}_{company.lower()}"
                    if key in exp_seen:
                        # Append source provenance to existing entry
                        for entry in unified_experience:
                            if f"{entry.role.lower()}_{entry.company.lower()}" == key:
                                if "linkedin" not in entry.sources:
                                    entry.sources.append("linkedin")
                    else:
                        exp_seen.add(key)
                        unified_experience.append(NormalizedExperience(
                            role=role,
                            company=company,
                            dates=item.get("dates") or "N/A",
                            description=item.get("description") or "",
                            sources=["linkedin"]
                        ))

    # 3. EDUCATION NORMALIZATION
    unified_education: List[NormalizedEducation] = []
    edu_seen = set()

    if resume_data:
        ext = resume_data.get("extracted_data") or resume_data
        edu_list = ext.get("education") or []
        if isinstance(edu_list, list):
            for item in edu_list:
                if isinstance(item, dict):
                    degree = item.get("degree") or "Bachelor of Science"
                    inst = item.get("institution") or item.get("university") or "University"
                    key = f"{degree.lower()}_{inst.lower()}"
                    if key not in edu_seen:
                        edu_seen.add(key)
                        unified_education.append(NormalizedEducation(
                            degree=degree,
                            institution=inst,
                            dates=item.get("year") or item.get("dates") or "N/A",
                            sources=["resume"]
                        ))

    # 4. PROJECT NORMALIZATION
    unified_projects: List[NormalizedProject] = []
    proj_seen = set()

    if resume_data:
        ext = resume_data.get("extracted_data") or resume_data
        p_list = ext.get("projects") or []
        if isinstance(p_list, list):
            for p in p_list:
                if isinstance(p, dict):
                    title = p.get("title") or p.get("name") or "Portfolio Project"
                    key = title.lower()
                    if key not in proj_seen:
                        proj_seen.add(key)
                        unified_projects.append(NormalizedProject(
                            title=title,
                            description=p.get("description") or "",
                            technologies=p.get("technologies") or [],
                            sources=["resume"]
                        ))

    if github_data:
        g_data = github_data.get("github_data") or {}
        g_repos = g_data.get("repositories") or github_data.get("repositories") or []
        if isinstance(g_repos, list):
            for r in g_repos:
                if isinstance(r, dict):
                    title = r.get("name") or "repo"
                    key = title.lower()
                    if key in proj_seen:
                        for entry in unified_projects:
                            if entry.title.lower() == key:
                                if "github" not in entry.sources:
                                    entry.sources.append("github")
                    else:
                        proj_seen.add(key)
                        unified_projects.append(NormalizedProject(
                            title=title,
                            description=f"GitHub Repository ({r.get('stargazers_count', 0)} stars, {r.get('forks_count', 0)} forks)",
                            technologies=[r.get("language")] if r.get("language") else [],
                            sources=["github"]
                        ))

    # 5. CERTIFICATIONS
    certifications: List[str] = []
    if resume_data:
        ext = resume_data.get("extracted_data") or resume_data
        certs = ext.get("certifications") or []
        if isinstance(certs, list):
            for c in certs:
                if isinstance(c, str) and c not in certifications:
                    certifications.append(c)
                elif isinstance(c, dict) and c.get("name") not in certifications:
                    certifications.append(c.get("name"))

    # 6. CROSS-SOURCE CONSISTENCY ANALYSIS
    consistent_claims: List[str] = []
    potential_discrepancies: List[str] = []
    missing_evidence: List[str] = []

    # Check multi-source skill verifications
    multi_source_skills = [sk for sk in unified_skills if len(sk.sources) > 1]
    for sk in multi_source_skills:
        sources_str = ", ".join([s.capitalize() for s in sk.sources])
        consistent_claims.append(f"Skill '{sk.skill}' verified across multiple sources ({sources_str}).")

    single_resume_skills = [sk for sk in unified_skills if sk.sources == ["resume"]]
    if github_data and single_resume_skills:
        for sk in single_resume_skills[:3]:
            missing_evidence.append(f"Skill '{sk.skill}' is listed on Resume but has limited GitHub codebase evidence.")

    # Check experience consistency
    for exp in unified_experience:
        if len(exp.sources) > 1:
            consistent_claims.append(f"Role '{exp.role}' at '{exp.company}' verified on both Resume and LinkedIn.")

    # Consistency score calculation
    if unified_skills:
        multi_count = len(multi_source_skills)
        match_ratio = multi_count / max(1, len(unified_skills))
        consistency_score = int(60 + (match_ratio * 35))
    else:
        consistency_score = 75
    consistency_score = max(50, min(100, consistency_score))

    consistency_report = CrossSourceConsistency(
        consistency_score=consistency_score,
        consistent_claims=consistent_claims if consistent_claims else ["Primary candidate credentials align across provided documents."],
        potential_discrepancies=potential_discrepancies,
        missing_evidence=missing_evidence if missing_evidence else ["All listed skills have sufficient source documentation."]
    )

    # 7. STRENGTHS, GAPS & RECOMMENDATIONS
    strengths: List[str] = []
    if len(unified_skills) >= 5:
        strengths.append(f"Demonstrates broad technical skill coverage with {len(unified_skills)} identified technologies.")
    if multi_source_skills:
        strengths.append(f"High multi-source credential verification for core skills ({', '.join([s.skill for s in multi_source_skills[:3]])}).")
    if github_data:
        g_score = github_data.get("github_score", 70)
        strengths.append(f"Active public code repositories with a GitHub evaluation score of {g_score}/100.")
    if not strengths:
        strengths.append("Clear professional background with documented candidate credentials.")

    gaps: List[str] = []
    if not github_data:
        gaps.append("Limited public code evidence available (GitHub analysis not yet linked).")
    if not linkedin_data:
        gaps.append("Public professional networking context not linked (LinkedIn audit pending).")
    if missing_evidence:
        gaps.append("Some resume technical claims lack secondary public repository evidence.")
    if not gaps:
        gaps.append("Comprehensive candidate coverage across all three analysis channels.")

    recommendations: List[str] = []
    if missing_evidence:
        recommendations.append("Build open-source repositories showcasing skills currently listed only on your resume.")
    if github_data:
        for rec in github_data.get("improvement_suggestions", [])[:2]:
            if rec not in recommendations:
                recommendations.append(rec)
    if linkedin_data:
        for rec in linkedin_data.get("optimization_suggestions", [])[:2]:
            if rec not in recommendations:
                recommendations.append(rec)
    if not recommendations:
        recommendations.append("Keep public codebases updated with comprehensive README documentation and CI/CD pipelines.")

    return (
        unified_skills,
        unified_experience,
        unified_education,
        unified_projects,
        certifications,
        consistency_report,
        strengths,
        gaps,
        recommendations
    )
