import os
from llm_helper import InterviewManager

def test_evaluation():
    manager = InterviewManager()
    
    print("--- Testing Intro Phase ---")
    intro_eval = manager.evaluate_answer(
        role="AI Engineer",
        question="Please introduce yourself and walk me through your relevant experience for this role.",
        answer="I am a BTech student with experience in AI and Python. I have worked on LangChain projects.",
        question_count=1
    )
    print(f"Score: {intro_eval['score']}/10")
    print(f"Feedback: {intro_eval['feedback']}")
    
    print("\n--- Testing Technical Phase ---")
    tech_eval = manager.evaluate_answer(
        role="AI Engineer",
        question="What is the difference between a Transformer and an RNN?",
        answer="Transformers use self-attention and can process sequences in parallel, unlike RNNs which are sequential.",
        question_count=2
    )
    print(f"Score: {tech_eval['score']}/10")
    print(f"Feedback: {tech_eval['feedback']}")

if __name__ == "__main__":
    test_evaluation()
