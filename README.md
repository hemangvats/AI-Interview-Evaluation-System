# 🚀 AI Interview Evaluation System

An AI-powered interview simulator that evaluates user responses using **local LLM-based scoring, structured feedback, and strict grading logic**.

---

## 🧠 Key Features

* 🎯 Role-based interview simulation (AI Engineer, etc.)
* 📊 AI-powered answer evaluation (score: 0–10)
* 🧾 Feedback + improvement suggestions
* ⚡ Strict grading system (relevance + accuracy checks)
* 🚫 Anti-filler detection (prevents generic answers)
* 🎚️ Adjustable difficulty levels

---

## ⚙️ Tech Stack

* Python
* Streamlit
* Ollama (LLaMA 3:3B)
* Prompt Engineering

---

## 🤖 LLM Integration (Ollama)

This project uses **Ollama (LLaMA 3:3B)** to run the language model locally instead of relying on external APIs.

### Why Ollama?

* ⚡ Runs locally (no API cost)
* 🔒 Better privacy (no data sent externally)
* 🚀 Faster responses for small-scale applications
* 🧠 Efficient for evaluation-based tasks

### Setup Ollama

1. Install Ollama:
   https://ollama.com/download

2. Pull the model:

```bash
ollama run llama3:3b
```

3. Ensure Ollama is running before starting the app

---

## 🧪 System Workflow

1. User selects role & difficulty
2. System generates interview questions
3. User submits answers
4. AI evaluates response using Ollama (LLaMA 3:3B):

   * Relevance Check
   * Accuracy Check
   * Anti-filler detection
   * Structured feedback generation
5. Returns:

   * Score (0–10)
   * Feedback
   * Suggestions

---

## 🧠 Evaluation Engine

The system uses LLM-based evaluation logic to:

* Detect irrelevant or filler answers
* Perform relevance and accuracy checks
* Generate structured feedback
* Assign strict scores (0–10)

This ensures realistic interview simulation and avoids lenient scoring behavior common in LLMs.

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🌐 Live Demo

🚀 Try the deployed app here:
👉 https://huggingface.co/spaces/Hemang18/AI-Interview-Bot

✅ Live deployed using Hugging Face Spaces

---

## 🚀 Future Improvements

* Resume-based question generation
* Score breakdown (relevance, accuracy, clarity)
* Performance analytics dashboard

---

## 🤝 Author

**Hemang Vats**
B.Tech CSE | AI/ML Enthusiast
