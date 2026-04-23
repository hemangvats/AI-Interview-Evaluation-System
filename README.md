---
title: AI Interview Bot
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🚀 AI Interview Evaluation System

An advanced AI-powered interview simulator that provides autonomous, role-based technical assessments using local LLMs. The system features real-time scoring, dynamic difficulty scaling, and comprehensive senior-level performance analytics to help candidates prepare for high-stakes technical interviews.

---

## 🧠 Key Features

* 🎯 **Phase-Based Assessment**: Specialized logic for *Candidate Introduction* and *Technical Assessment* phases.
* 📊 **Senior Hiring Manager Reports**: Generates a professional performance summary including Executive Summary, Key Strengths, Technical Gaps, and a Development Roadmap.
* 🎚️ **Dynamic Difficulty Adjustment**: The AI interviewer autonomously adjusts question difficulty (Beginner, Intermediate, Advanced) based on the candidate's real-time performance.
* ⚡ **Strict Grading Engine**: Built-in relevance and accuracy checks to prevent generic "filler" answers from scoring points.
* 📄 **Resume Integration**: Upload your resume (PDF/TXT) for a personalized interview experience tailored to your background.
* 🤖 **Autonomous Conclusion**: The AI decides when it has gathered enough information to provide a final hiring verdict.

---

## ⚙️ Tech Stack

* **Frontend**: Streamlit
* **AI Logic**: LangChain & Ollama (LLaMA 3.2:3B)
* **Language**: Python
* **Deployment**: Docker & Hugging Face Spaces

---

## 🤖 LLM Integration (Ollama)

This project uses **Ollama (LLaMA 3.2:3B)** to run the language model locally, ensuring privacy and speed without external API costs.

### Setup Ollama

1. Install Ollama: [https://ollama.com/download](https://ollama.com/download)
2. Pull the model:
   ```bash
   ollama run llama3.2:3b
   ```
3. Ensure Ollama is running before starting the app.

---

## 🧪 System Workflow

1. **Configuration**: User selects a role and optionally uploads a resume.
2. **Initial Phase**: Starts with a candidate introduction and experience walkthrough.
3. **Technical Phase**: System generates role-specific technical questions.
4. **Real-time Evaluation**: 
   * AI scores each answer (0–10).
   * Provides immediate feedback and improvement suggestions.
   * Adjusts difficulty for the next question based on the current score.
5. **Conclusion**: Once the AI has sufficient data (min 5-8 exchanges), it concludes the interview.
6. **Reporting**: Generates a deep-dive performance report and hiring verdict.

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🌐 Live Demo

🚀 Try the deployed app here:
👉 [https://huggingface.co/spaces/Hemang18/AI-Interview-Bot](https://huggingface.co/spaces/Hemang18/AI-Interview-Bot)

✅ Live deployed using Hugging Face Spaces

---

## 🚀 Future Improvements

* Audio-based interview mode (Speech-to-Text & Text-to-Speech).
* Multi-model support (Gemma 2, Mistral).
* Exportable PDF reports.

---

## 🤝 Author

**Hemang Vats**
B.Tech CSE | AI/ML Enthusiast

