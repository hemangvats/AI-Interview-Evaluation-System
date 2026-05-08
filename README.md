---
title: AI Interview Bot
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🚀 AI Interview Evaluation System

An advanced AI-powered interview simulator that provides autonomous, role-based technical assessments using local LLMs with **Cloud Persistence via Supabase**. The system features real-time scoring, **Autonomous Adaptive difficulty scaling**, and comprehensive senior-level performance analytics to help candidates prepare for high-stakes technical interviews.

---

## 🧠 Key Features

* 🎯 **Phase-Based Assessment**: Specialized logic for *Candidate Introduction* and *Technical Assessment* phases.
* 📊 **Senior Hiring Manager Reports**: Generates a professional performance summary including Executive Summary, Key Strengths, Technical Gaps, and a Development Roadmap.
* 🎚️ **Autonomous Adaptive Difficulty**: The AI interviewer autonomously adjusts question difficulty (Beginner, Intermediate, Advanced) in real-time based on your performance.
* ☁️ **Cloud Persistence (Supabase)**: All interview records are automatically synced to the cloud, allowing you to access your history from anywhere.
* ⚡ **Strict Grading Engine**: Built-in relevance and accuracy checks to prevent generic "filler" answers from scoring points.
* 📄 **Resume Integration**: Upload your resume (PDF/TXT) for a personalized interview experience tailored to your background.
* 🤖 **Autonomous Conclusion**: The AI decides when it has gathered enough information to provide a final hiring verdict.

---

## ⚙️ Tech Stack

* **Frontend**: Streamlit
* **AI Logic**: LangChain & Ollama (LLaMA 3.2:3B)
* **Database**: Supabase (PostgreSQL)
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

## 🛠️ Environment Setup

Create a `.env` file in the root directory and add your Supabase credentials:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
```

---

## 🧪 System Workflow

1. **Configuration**: User selects a role and optionally uploads a resume for personalized context.
2. **Initial Phase**: Starts with a candidate introduction and experience walkthrough.
3. **Technical Assessment**: System generates role-specific technical questions based on industry standards.
4. **Evaluation & Adaptive Scaling**: 
   * AI scores each answer (0–10) using a strict grading engine.
   * Provides immediate feedback and improvement suggestions.
   * Automatically scales difficulty for the next question based on performance.
5. **Cloud Persistence**: Every exchange is instantly synced to **Supabase Cloud** for a persistent, multi-device history.
6. **Autonomous Conclusion**: The AI interviewer decides when it has gathered enough high-quality data to provide a reliable hiring verdict.
7. **Comprehensive Reporting**: Generates a deep-dive performance report including technical gaps and a hiring verdict.

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

