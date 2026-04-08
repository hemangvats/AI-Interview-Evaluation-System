import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

load_dotenv()

class QuestionEvaluation(BaseModel):
    score: int = Field(description="Score out of 10")
    feedback: str = Field(description="Feedback on the answer, including strengths and weaknesses")
    suggestions: str = Field(description="Suggestions for improvement, such as real-world examples or technical terms to include")

# Keywords and patterns that instantly disqualify an answer
INVALID_ANSWER_PHRASES = [
    "idk", "i don't know", "i do not know", "dont know", "don't know",
    "no idea", "not sure", "i have no idea", "i don't have an answer",
    "pass", "skip", "n/a", "na", "none", "nothing", "?", "??", "???",
    "i give up", "no answer", "blank", "i am ready", "im ready", "ready",
]

def is_invalid_answer(answer: str) -> bool:
    """Check if the answer is gibberish, blank, or a dodge phrase."""
    stripped = answer.strip().lower()

    # Empty or whitespace only
    if not stripped:
        return True

    # Very short answer (less than 5 meaningful chars)
    if len(stripped) < 5:
        return True

    # Exact match against known dodge phrases
    if stripped in INVALID_ANSWER_PHRASES:
        return True

    # Partial match against dodge phrases
    for phrase in INVALID_ANSWER_PHRASES:
        if phrase in stripped:
            return True

    # Gibberish detection: if less than 50% of chars are alphabetic/space, it is likely garbage
    alpha_chars = sum(1 for c in stripped if c.isalpha() or c.isspace())
    if len(stripped) > 0 and (alpha_chars / len(stripped)) < 0.5:
        return True

    # Check for repeated characters (e.g. "aaaaaaa", "bbbbb")
    if len(set(stripped.replace(" ", ""))) < 3 and len(stripped) > 3:
        return True

    return False


class InterviewManager:
    def __init__(self):
        # Initialize LLM with Ollama
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = ChatOllama(model="llama3.2:3b", temperature=0.7, base_url=base_url)

    def generate_questions(self, role: str, num_questions: int = 5, difficulty: str = "Intermediate", resume_text: str = "") -> list[str]:
        if resume_text.strip():
            template = "You are an expert technical interviewer. Generate {num_questions} {difficulty} level technical interview questions for a {role} position. Use the candidate's following resume to tailor at least some of the questions to their experience: {resume_text}. Provide only the questions, one per line, without numbering or any other text."
            input_variables = ["role", "num_questions", "difficulty", "resume_text"]
            prompt = PromptTemplate(template=template, input_variables=input_variables)
            chain = prompt | self.llm
            response = chain.invoke({"role": role, "num_questions": num_questions, "difficulty": difficulty, "resume_text": resume_text})
        else:
            template = "You are an expert technical interviewer. Generate {num_questions} {difficulty} level technical interview questions for a {role} position. Provide only the questions, one per line, without numbering or any other text."
            input_variables = ["role", "num_questions", "difficulty"]
            prompt = PromptTemplate(template=template, input_variables=input_variables)
            chain = prompt | self.llm
            response = chain.invoke({"role": role, "num_questions": num_questions, "difficulty": difficulty})
        questions = [q.strip() for q in response.content.split("\n") if q.strip()]
        return questions[:num_questions]

    def evaluate_answer(self, role: str, question: str, answer: str, difficulty: str = "Intermediate", resume_text: str = "") -> dict:
        # ----------------------------------------------------------------
        # Layer 1: Python pre-check — catches gibberish/blanks/idk BEFORE
        # wasting an LLM call. Score is always hard 0, no negotiation.
        # ----------------------------------------------------------------
        if is_invalid_answer(answer):
            return {
                "score": 0,
                "feedback": (
                    "❌ Your answer was not valid. It appears to be blank, gibberish, "
                    "or a non-answer (e.g. 'idk', random characters, or whitespace). "
                    "No credit can be awarded for this response."
                ),
                "suggestions": (
                    "Please attempt to answer the question properly. "
                    "Even a partial answer earns more credit than no answer. "
                    "Study the topic and try explaining it in your own words."
                )
            }

        # ----------------------------------------------------------------
        # Layer 2: LLM evaluation with an ultra-strict scoring prompt
        # ----------------------------------------------------------------
        parser = JsonOutputParser(pydantic_object=QuestionEvaluation)

        template = """You are a strict and fair technical interviewer for a {difficulty} level {role} position.

The candidate was asked:
Question: {question}

The candidate answered:
Answer: {answer}"""
        
        if resume_text.strip():
            template += """\n\nThe candidate's Resume is provided below. You can use it to determine if their answer aligns with their claimed experience.
Resume: {resume_text}"""
        
        template += """\n\nCRITICAL SCORING INSTRUCTIONS. YOU ARE AN UNCOMPROMISING ASSESSOR:
1. RELEVANCE CHECK: Does the Answer explicitly and technically address the exact Question? If it is a generic statement like "I am ready", "yes", "no", "let's go", or completely changes the subject, you MUST assign a score of 0.
2. ACCURACY CHECK: If the answer provides factually incorrect technical information for the given role, you MUST assign a 0 or 1.
3. SCORING RUBRIC:
   - 0: Completely irrelevant (e.g., "I'm ready"), totally incorrect, or dodges the question.
   - 1 to 3: Flawed attempt, very poor technical understanding.
   - 4 to 6: Partially correct but missing major components.
   - 7 to 8: Good answer, demonstrates clear understanding with minor gaps.
   - 9 to 10: Outstanding, comprehensive, and accurate response.

DO NOT BE LENIENT. It is better to give a 0 than to mistakenly award marks for confident nonsense.
You MUST output ONLY a valid JSON object. Do not add any text outside the JSON.

{format_instructions}
"""
        
        input_vars = ["role", "question", "answer", "difficulty"]
        if resume_text.strip():
            input_vars.append("resume_text")
            
        prompt = PromptTemplate(
            template=template,
            input_variables=input_vars,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | self.llm.bind(format="json") | parser
        try:
            invoke_args = {"role": role, "question": question, "answer": answer, "difficulty": difficulty}
            if resume_text.strip():
                invoke_args["resume_text"] = resume_text
                
            result = chain.invoke(invoke_args)
            if not isinstance(result, dict):
                raise ValueError("LLM output is not a dict.")

            # Ensure all required keys exist
            result.setdefault("score", 0)
            result.setdefault("feedback", "The evaluation model did not provide feedback.")
            result.setdefault("suggestions", "Review the topic and try again.")

            # Clamp score to 0-10 range
            try:
                result["score"] = max(0, min(10, int(result["score"])))
            except (ValueError, TypeError):
                result["score"] = 0

            return result

        except Exception:
            return {
                "score": 0,
                "feedback": "The AI evaluator encountered an error processing this response. It has been marked as invalid.",
                "suggestions": "Try providing a clearly structured and relevant answer next time."
            }
