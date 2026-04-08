import streamlit as st
import os
import json
import datetime
from llm_helper import InterviewManager

# Ensure history directory exists
HISTORY_DIR = "chat_history"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def save_chat_history():
    if "session_id" in st.session_state and st.session_state.messages:
        file_path = os.path.join(HISTORY_DIR, f"{st.session_state.session_id}.json")
        data = {
            "role": st.session_state.selected_role,
            "difficulty": st.session_state.selected_difficulty,
            "timestamp": st.session_state.session_id,
            "messages": st.session_state.messages,
            "evaluations": st.session_state.evaluations,
            "interview_complete": st.session_state.interview_complete
        }
        try:
            with open(file_path, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

st.set_page_config(page_title="AI Interview Prep Bot", page_icon="🤖", layout="wide")

# Initialize Session State
if "interview_manager" not in st.session_state:
    try:
        st.session_state.interview_manager = InterviewManager()
    except Exception as e:
        st.error("Error initializing LLM. Please ensure Ollama is running and the llama3.2:3b model is pulled.")
        st.stop()

if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_q_index" not in st.session_state:
    st.session_state.current_q_index = 0
if "evaluations" not in st.session_state:
    st.session_state.evaluations = []
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False
if "selected_role" not in st.session_state:
    st.session_state.selected_role = ""
if "selected_difficulty" not in st.session_state:
    st.session_state.selected_difficulty = "Intermediate"
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# Remove default title to mimic clean ChatGPT layout
# st.title("🤖 AI Interview Preparation Bot")

# Sidebar for settings
with st.sidebar:
    if st.button("➕ New Interview", use_container_width=True):
        st.session_state.interview_active = False
        st.session_state.interview_complete = False
        st.session_state.messages = []
        st.session_state.questions = []
        st.session_state.evaluations = []
        if "session_id" in st.session_state:
            del st.session_state.session_id
        st.rerun()
        
    st.divider()
    st.header("Recents")
    history_files = sorted(os.listdir(HISTORY_DIR), reverse=True)
    if not history_files:
        st.caption("No recent interviews.")
    for hf in history_files:
        if not hf.endswith(".json"): continue
        try:
            with open(os.path.join(HISTORY_DIR, hf), "r") as f:
                hdata = json.load(f)
            # Create a label with date and role
            date_str = hdata.get("timestamp", hf.replace(".json", ""))[:8]
            display_date = f"{date_str[4:6]}/{date_str[6:8]}" if len(date_str) == 8 else date_str
            btn_label = f"💬 {hdata.get('role', 'Interview')} - {display_date}"
            
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(btn_label, key=f"load_{hf}", use_container_width=True, help="Load this conversation"):
                    st.session_state.session_id = hf.replace(".json", "")
                    st.session_state.messages = hdata.get("messages", [])
                    st.session_state.evaluations = hdata.get("evaluations", [])
                    st.session_state.interview_complete = hdata.get("interview_complete", False)
                    st.session_state.selected_role = hdata.get("role", "")
                    st.session_state.selected_difficulty = hdata.get("difficulty", "")
                    st.session_state.interview_active = not st.session_state.interview_complete
                    st.rerun()
                    
            with col2:
                if st.button("🗑️", key=f"del_{hf}", use_container_width=True, help="Delete conversation"):
                    try:
                        os.remove(os.path.join(HISTORY_DIR, hf))
                        if st.session_state.get("session_id") == hf.replace(".json", ""):
                            # Reset if the deleted chat is currently active
                            st.session_state.interview_active = False
                            st.session_state.interview_complete = False
                            st.session_state.messages = []
                            st.session_state.evaluations = []
                            del st.session_state.session_id
                    except Exception:
                        pass
                    st.rerun()
        except Exception:
            pass

    st.divider()
    st.header("Interview Settings")
    roles = ["AI Engineer", "Software Developer", "Data Scientist", "Web Developer", "Frontend Developer", "Backend Developer"]
    
    # We use a key so Streamlit tracks it, but we also save to session state when beginning
    selected_role_input = st.selectbox("Select Role", roles)
    difficulties = ["Beginner", "Intermediate", "Advanced"]
    selected_difficulty_input = st.selectbox("Select Difficulty", difficulties)
    num_questions_input = st.slider("Number of Questions", min_value=3, max_value=10, value=5)
    
    st.divider()
    st.subheader("Personalize (Optional)")
    resume_file = st.file_uploader("Upload Resume (PDF/TXT)", type=["pdf", "txt"])
    
    if st.button("Start Interview"):
        st.session_state.selected_role = selected_role_input
        st.session_state.selected_difficulty = selected_difficulty_input
        
        # Parse resume if provided
        st.session_state.resume_text = ""
        if resume_file is not None:
            if resume_file.name.endswith(".pdf"):
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(resume_file)
                    st.session_state.resume_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                except Exception as e:
                    st.warning(f"Error parsing PDF: {e}")
            else:
                try:
                    st.session_state.resume_text = resume_file.read().decode("utf-8")
                except Exception as e:
                    st.warning(f"Error reading TXT: {e}")
                    
        with st.spinner("Generating questions..."):
            st.session_state.questions = st.session_state.interview_manager.generate_questions(
                selected_role_input, num_questions_input, selected_difficulty_input, st.session_state.resume_text
            )
            st.session_state.current_q_index = 0
            st.session_state.evaluations = []
            
            # Initialize bot's first chat message
            st.session_state.messages = [{
                "role": "assistant", 
                "content": f"Hello! I will be interviewing you for the **{selected_role_input}** position today. Let's begin.\n\n**Question 1/{len(st.session_state.questions)}:** {st.session_state.questions[0]}"
            }]
            
            st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.interview_active = True
            st.session_state.interview_complete = False
            
            save_chat_history()
            st.rerun()

# Main Interview Area
if st.session_state.interview_active or st.session_state.interview_complete:
    st.header(f"Interviewing for: {st.session_state.selected_role} ({st.session_state.selected_difficulty} Level)")
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input 
    if st.session_state.interview_active:
        if prompt := st.chat_input("Type your answer here..."):
            
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Evaluating your answer..."):
                    current_question = st.session_state.questions[st.session_state.current_q_index]
                    
                    evaluation = st.session_state.interview_manager.evaluate_answer(
                        st.session_state.selected_role, current_question, prompt, 
                        st.session_state.selected_difficulty, st.session_state.resume_text
                    )
                    
                    st.session_state.evaluations.append({
                        "question": current_question,
                        "answer": prompt,
                        "evaluation": evaluation
                    })
                    
                    score = evaluation['score']
                    color = "green" if score >= 8 else "orange" if score >= 5 else "red"
                    
                    # Construct feedback
                    feedback_msg = f"**Previous Reply Feedback**:\n"
                    feedback_msg += f"- **Score**: :{color}[{score}/10]\n"
                    feedback_msg += f"- **Feedback**: {evaluation['feedback']}\n"
                    feedback_msg += f"- **Improvement**: {evaluation['suggestions']}\n\n---\n\n"
                    
                    st.session_state.current_q_index += 1
                    
                    # Next Question logic
                    if st.session_state.current_q_index < len(st.session_state.questions):
                        next_q = st.session_state.questions[st.session_state.current_q_index]
                        feedback_msg += f"**Question {st.session_state.current_q_index + 1}/{len(st.session_state.questions)}:** {next_q}"
                    else:
                        feedback_msg += "🎉 **Interview Complete!** You have answered all questions. You can review our chat history above."
                        st.session_state.interview_active = False
                        st.session_state.interview_complete = True
                        
                    st.session_state.messages.append({"role": "assistant", "content": feedback_msg})
                    save_chat_history()
                    st.rerun()

    elif st.session_state.interview_complete:
        st.divider()
        col1, col2 = st.columns(2)
        total_score = sum(e["evaluation"]["score"] for e in st.session_state.evaluations)
        avg_score = total_score / len(st.session_state.evaluations) if st.session_state.evaluations else 0
        
        col1.metric("Total Questions", len(st.session_state.evaluations))
        col2.metric("Average Final Score", f"{avg_score:.1f}/10")
        
        if st.button("Start New Interview", type="primary"):
            st.session_state.interview_complete = False
            st.session_state.messages = []
            st.rerun()
                    


else:
    # ChatGPT empty state mockup
    st.markdown("""
    <style>
    .empty-state {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 70vh;
        text-align: center;
    }
    .empty-state h1 {
        font-size: 32px;
        font-weight: 600;
        margin-bottom: 20px;
        color: #ececf1;
    }
    </style>
    <div class="empty-state">
        <h1>Where should we begin?</h1>
        <p style='color: #888;'>Configure your role and difficulty in the sidebar, then click <b>Start Interview</b> to begin your conversation.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render a disabled chat input just for the visual aesthetic at the bottom
    st.chat_input("Configure sidebar to start...", disabled=True)
