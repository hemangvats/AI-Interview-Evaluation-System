import os
from dotenv import load_dotenv
import datetime
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

load_dotenv()

class QuestionEvaluation(BaseModel):
    """Pydantic model for structured LLM evaluation output."""
    score: int = Field(description="Score out of 10")
    feedback: str = Field(description="Feedback on the answer, including strengths and weaknesses")
    suggestions: str = Field(description="Actionable technical suggestions for improvement")
    difficulty_adjustment: str = Field(description="Recommendation for the next question: 'increase', 'decrease', or 'stay'")
    follow_up_question: str = Field(description="Contextual follow-up question. Leave empty if moving to a new topic.")
    is_interview_complete: bool = Field(description="True if enough info is gathered for a final hiring decision.")
    hiring_decision: str = Field(description="Final verdict: 'Strong Hire', 'Hire', 'Leaning No Hire', or 'No Hire'.")
    verdict_reasoning: str = Field(description="Comprehensive reasoning for the final verdict.")

# Keywords and patterns that instantly disqualify an answer as gibberish or a dodge
INVALID_ANSWER_PHRASES = {
    "idk", "i don't know", "i do not know", "dont know", "don't know",
    "no idea", "not sure", "i have no idea", "i don't have an answer",
    "pass", "skip", "n/a", "na", "none", "nothing", "?", "??", "???",
    "i give up", "no answer", "blank", "i am ready", "im ready", "ready",
}

def is_invalid_answer(answer: str) -> bool:
    """
    Performs multi-layered validation on the candidate's answer to filter out
    gibberish, dodging, or low-effort responses. Uses word-boundary checks
    to avoid false positives with typos.
    """
    import re
    stripped = answer.strip().lower()

    if not stripped or len(stripped) < 4:
        return True

    # Check for exact matches or whole-word matches of dodge phrases
    for phrase in INVALID_ANSWER_PHRASES:
        # Use regex to match the phrase as a whole word only
        pattern = rf"\b{re.escape(phrase)}\b"
        if re.search(pattern, stripped):
            return True

    # Gibberish check: verify character diversity
    # Only flag as gibberish if it's very long and has almost no variety
    if len(stripped) > 20 and len(set(stripped.replace(" ", ""))) < 5:
        return True

    return False


class InterviewManager:
    """Manages the interview lifecycle, from question generation to structured evaluation."""

    def __init__(self):
        # Configure the local LLM via Ollama
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = ChatOllama(model="llama3.2:3b", temperature=0.7, base_url=base_url)

    def generate_questions(self, role: str, num_questions: int = 1, difficulty: str = "Intermediate", 
                           resume_text: str = "", previous_questions: list[str] = None, 
                           is_behavioral: bool = False) -> list[str]:
        """Generates contextual and non-repetitive interview questions."""
        
        prev_q_str = f" Avoid these previously asked questions: {', '.join(previous_questions)}." if previous_questions else ""
        q_type = "behavioral (STAR method)" if is_behavioral else "technical"
        
        template = (
            "You are an expert technical interviewer. Generate {num_questions} {difficulty} level {q_type} "
            "interview questions for a {role} position. "
        )
        
        if resume_text.strip():
            template += "Use the candidate's resume to tailor the questions: {resume_text}. "
            
        template += "{prev_q_str} Provide only the questions, one per line, without numbering or extra text."

        prompt = PromptTemplate(
            template=template, 
            input_variables=["role", "num_questions", "difficulty", "resume_text", "prev_q_str", "q_type"]
        )
        
        chain = prompt | self.llm
        response = chain.invoke({
            "role": role, "num_questions": num_questions, "difficulty": difficulty, 
            "resume_text": resume_text, "prev_q_str": prev_q_str, "q_type": q_type
        })
        
        questions = [q.strip() for q in response.content.split("\n") if q.strip()]
        return questions[:num_questions]

    def evaluate_answer(self, role: str, question: str, answer: str, 
                        difficulty: str = "Intermediate", resume_text: str = "", 
                        question_count: int = 1) -> dict:
        """Evaluates a candidate's answer with technical rigor and contextual awareness."""

        if is_invalid_answer(answer):
            return {
                "score": 0,
                "feedback": "❌ The response was invalid, blank, or did not attempt to answer the question.",
                "suggestions": "Please provide a specific and relevant technical answer to receive credit.",
                "difficulty_adjustment": "decrease",
                "follow_up_question": "",
                "is_interview_complete": False,
                "hiring_decision": "",
                "verdict_reasoning": ""
            }

        parser = JsonOutputParser(pydantic_object=QuestionEvaluation)
        is_intro = (question_count == 1)
        phase_name = "Candidate Introduction" if is_intro else "Technical Assessment"
        
        template = """You are a senior professional technical interviewer for a {difficulty} level {role} role.
Current Progress: Question {question_count}
Phase: {phase_name}

Candidate Question: {question}
Candidate Answer: {answer}"""
        
        if resume_text.strip():
            template += "\n\nCandidate Resume: {resume_text}"
        
        template += """\n\nSCORING PROTOCOL:
1. PHASE SPECIFICITY:
   - If Introduction: Score (0-10) based on communication, professional history, and clarity.
   - If Technical: Score (0-10) based on technical accuracy, depth, and problem-solving logic.
2. RELEVANCE: Score 0 if the answer is completely unrelated to the field or specific question.
3. COMPLETION:
   - Decide if you have enough information to make a final hiring decision.
   - **CRITICAL**: An interview MUST last at least 5-8 exchanges to be fair. Never end after just 1 or 2 questions.
   - If Progress < 5, always set `is_interview_complete` to false.
4. LOGIC: Never recommend a difficulty 'increase' if the score is below 6/10.

Output your evaluation in strict JSON format.

{format_instructions}
"""
        
        input_vars = ["role", "question", "answer", "difficulty", "question_count", "phase_name"]
        if resume_text.strip():
            input_vars.append("resume_text")
            
        prompt = PromptTemplate(
            template=template,
            input_variables=input_vars,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | self.llm.bind(format="json") | parser
        
        try:
            result = chain.invoke({
                "role": role, "question": question, "answer": answer, 
                "difficulty": difficulty, "question_count": question_count,
                "phase_name": phase_name, "resume_text": resume_text
            })
            
            # Default fallback for missing keys
            defaults = {
                "score": 0, "feedback": "Evaluation failed.", "suggestions": "N/A",
                "difficulty_adjustment": "stay", "follow_up_question": "",
                "is_interview_complete": False, "hiring_decision": "", "verdict_reasoning": ""
            }
            for key, val in defaults.items():
                result.setdefault(key, val)
                
            return result

        except Exception as e:
            return {
                "score": 0, "feedback": f"System Error: {str(e)}", "suggestions": "Retrying might help.",
                "difficulty_adjustment": "stay", "follow_up_question": "",
                "is_interview_complete": False, "hiring_decision": "", "verdict_reasoning": ""
            }

    def generate_final_summary(self, role: str, evaluations: list[dict]) -> str:
        """Synthesizes all interview data into a professional performance report."""
        
        if not evaluations:
            return "Interview data unavailable."
            
        summary_prompt = f"Review this {role} interview transcript and provide a senior hiring manager's report.\n\n"
        
        for i, ev in enumerate(evaluations):
            summary_prompt += f"Q{i+1}: {ev['question']}\nA: {ev['answer']}\nScore: {ev['evaluation']['score']}/10\n\n"
            
        summary_prompt += """
Format the report with these sections:
## 📊 Executive Summary
## ✅ Key Strengths
## ❌ Technical Gaps & Mistakes
## 📚 Personal Development Roadmap (3 actionable steps)
"""

        response = self.llm.invoke(summary_prompt)
        return response.content
