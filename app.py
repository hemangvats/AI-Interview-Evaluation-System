import streamlit as st
import os
import json
import datetime
from llm_helper import InterviewManager

# --- CONFIG ---
st.set_page_config(page_title="AI Interview Bot", page_icon="🤖", layout="wide")

HISTORY_DIR = "interview_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

def save_chat_history():
    if "session_id" in st.session_state and st.session_state.messages:
        file_path = os.path.join(HISTORY_DIR, f"{st.session_state.session_id}.json")
        data = {
            "role": st.session_state.selected_role,
            "difficulty": st.session_state.selected_difficulty,
            "timestamp": st.session_state.session_id,
            "messages": st.session_state.messages,
            "evaluations": st.session_state.evaluations,
            "interview_complete": st.session_state.interview_complete,
            "final_summary": st.session_state.get("final_summary", ""),
            "total_questions": st.session_state.get("total_questions", 15),
            "questions": st.session_state.get("questions", []),
            "current_q_index": st.session_state.get("current_q_index", 0),
            "hiring_decision": st.session_state.get("hiring_decision", ""),
            "verdict_reasoning": st.session_state.get("verdict_reasoning", "")
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
if "final_summary" not in st.session_state:
    st.session_state.final_summary = ""
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 15
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_q_index" not in st.session_state:
    st.session_state.current_q_index = 0

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
            
            col1, col2 = st.columns([6, 1])
            with col1:
                if st.button(btn_label, key=f"load_{hf}", use_container_width=True):
                    st.session_state.session_id = hf.replace(".json", "")
                    st.session_state.messages = hdata.get("messages", [])
                    st.session_state.evaluations = hdata.get("evaluations", [])
                    st.session_state.interview_complete = hdata.get("interview_complete", False)
                    st.session_state.final_summary = hdata.get("final_summary", "")
                    st.session_state.total_questions = hdata.get("total_questions", 15)
                    st.session_state.questions = hdata.get("questions", [])
                    st.session_state.current_q_index = hdata.get("current_q_index", 0)
                    st.session_state.selected_role = hdata.get("role", "")
                    st.session_state.selected_difficulty = hdata.get("difficulty", "")
                    st.session_state.hiring_decision = hdata.get("hiring_decision", "N/A")
                    st.session_state.verdict_reasoning = hdata.get("verdict_reasoning", "No reasoning provided.")
                    st.session_state.interview_active = not st.session_state.interview_complete
                    st.rerun()
                    
            with col2:
                if st.button("🗑️", key=f"del_{hf}", use_container_width=True):
                    try:
                        os.remove(os.path.join(HISTORY_DIR, hf))
                        if st.session_state.get("session_id") == hf.replace(".json", ""):
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
    st.info("🎯 **AI-Driven Interview**: The interviewer will autonomously decide when it has enough information to reach a hiring decision.")
    
    st.divider()
    st.subheader("Personalize (Optional)")
    resume_file = st.file_uploader("Upload Resume (PDF/TXT)", type=["pdf", "txt"])
    
    if st.button("Start Interview"):
        st.session_state.selected_role = selected_role_input
        st.session_state.selected_difficulty = "Intermediate" 
        st.session_state.total_questions = 15 # Safety limit
        st.session_state.hiring_decision = None
        st.session_state.verdict_reasoning = ""
        st.session_state.final_summary = ""
        
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
                    
        with st.spinner("Initializing interview..."):
            st.session_state.questions = ["Introduction and Candidate Walkthrough"]
            st.session_state.current_q_index = 0
            st.session_state.evaluations = []
            st.session_state.interview_phase = "intro"
            
            # Initialize bot's first chat message
            st.session_state.messages = [{
                "role": "assistant", 
                "content": f"Hello! I am your AI Interviewer today. I'll be evaluating your fit for the **{selected_role_input}** position.\n\nPlease introduce yourself and walk me through your relevant experience for this role."
            }]
            
            st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.interview_active = True
            st.session_state.interview_complete = False
            
            save_chat_history()
            st.rerun()

# Main Interview Area
if st.session_state.interview_active or st.session_state.interview_complete:
    st.header(f"Interviewing for: {st.session_state.selected_role}")
    
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
                        st.session_state.selected_difficulty, st.session_state.resume_text,
                        st.session_state.current_q_index + 1
                    )
                    
                    st.session_state.evaluations.append({
                        "question": current_question,
                        "answer": prompt,
                        "evaluation": evaluation
                    })
                    
                    score = evaluation.get("score", 0)
                    score_color = "green" if score >= 8 else "orange" if score >= 5 else "red"
                    
                    feedback_msg = f"**Previous Reply Feedback**:\n"
                    feedback_msg += f"- **Score**: :{score_color}[{score}/10]\n"
                    feedback_msg += f"- **Feedback**: {evaluation['feedback']}\n"
                    feedback_msg += f"- **Improvement**: {evaluation['suggestions']}\n"
                    
                    # Difficulty Adjustment UI Logic
                    diff_levels = ["Beginner", "Intermediate", "Advanced"]
                    curr_idx = diff_levels.index(st.session_state.selected_difficulty)
                    adj = evaluation.get("difficulty_adjustment", "stay")
                    
                    if adj == "increase" and curr_idx < 2 and score >= 6:
                        st.session_state.selected_difficulty = diff_levels[curr_idx + 1]
                        feedback_msg += f"\n📈 *Great job! Increasing difficulty to **{st.session_state.selected_difficulty}** for the next question.*\n"
                    elif adj == "decrease" and curr_idx > 0 and score < 5:
                        st.session_state.selected_difficulty = diff_levels[curr_idx - 1]
                        feedback_msg += f"\n📉 *Adjusting difficulty to **{st.session_state.selected_difficulty}** to help you build confidence.*\n"
                    
                    feedback_msg += "\n---\n"
                    st.session_state.current_q_index += 1
                    
                    # Phase Transition (Internal only)
                    if st.session_state.current_q_index == 1:
                        st.session_state.interview_phase = "technical"
                    
                    # Completion check (Minimum 4 exchanges for a fair assessment)
                    min_questions = 4
                    llm_wants_to_end = evaluation.get("is_interview_complete", False)
                    
                    if (llm_wants_to_end and st.session_state.current_q_index >= min_questions) or st.session_state.current_q_index >= st.session_state.total_questions:
                        feedback_msg += "\n🎉 **Interview Complete!** I have gathered enough information for a final verdict. See below."
                        st.session_state.interview_active = False
                        st.session_state.interview_complete = True
                        
                        # Capture verdict from the last evaluation
                        st.session_state.hiring_decision = evaluation.get("hiring_decision", "")
                        st.session_state.verdict_reasoning = evaluation.get("verdict_reasoning", "")
                        
                        # Fallback: If AI didn't provide a verdict (e.g., hit hard limit), generate one now
                        if not st.session_state.hiring_decision:
                            with st.spinner("Calculating final hiring verdict..."):
                                # We can derive this from the evaluations or ask the LLM one last time
                                summary_data = st.session_state.interview_manager.evaluate_answer(
                                    st.session_state.selected_role, "Final Review", "System concluding interview.",
                                    st.session_state.selected_difficulty, st.session_state.resume_text,
                                    st.session_state.current_q_index
                                )
                                st.session_state.hiring_decision = summary_data.get("hiring_decision", "Decision Pending")
                                st.session_state.verdict_reasoning = summary_data.get("verdict_reasoning", "The candidate reached the maximum number of questions.")
                        
                        # Generate final deep-dive summary
                        with st.spinner("Preparing your detailed performance report..."):
                            st.session_state.final_summary = st.session_state.interview_manager.generate_final_summary(
                                st.session_state.selected_role, st.session_state.evaluations
                            )
                    else:
                        follow_up = evaluation.get("follow_up_question", "")
                        
                        if follow_up and st.session_state.interview_phase == "technical":
                            next_q = follow_up
                            feedback_msg += f"🔍 *Follow-up Question:*\n"
                        else:
                            with st.spinner("Preparing next question..."):
                                is_closing = st.session_state.current_q_index >= 7 
                                next_q_list = st.session_state.interview_manager.generate_questions(
                                    st.session_state.selected_role, 1, st.session_state.selected_difficulty, 
                                    st.session_state.resume_text, st.session_state.questions, is_behavioral=is_closing
                                )
                                next_q = next_q_list[0]
                        
                        st.session_state.questions.append(next_q)
                        feedback_msg += f"**Question {st.session_state.current_q_index + 1}:** {next_q}"
                        
                    st.session_state.messages.append({"role": "assistant", "content": feedback_msg})
                    save_chat_history()
                    st.rerun()
                        
                    st.session_state.messages.append({"role": "assistant", "content": feedback_msg})
                    save_chat_history()
                    st.rerun()

    elif st.session_state.interview_complete:
        st.divider()
        st.subheader("📑 Detailed Performance Report")
        if st.session_state.final_summary:
            st.markdown(st.session_state.final_summary)
        
        st.divider()
        c1, c2 = st.columns(2)
        avg_score = sum(e["evaluation"]["score"] for e in st.session_state.evaluations) / len(st.session_state.evaluations) if st.session_state.evaluations else 0
        c1.metric("Exchanges", len(st.session_state.evaluations))
        c2.metric("Avg Technical Score", f"{avg_score:.1f}/10")
        
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
