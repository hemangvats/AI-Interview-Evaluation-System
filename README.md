---
title: AI Interview Bot
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# AI Interview Preparation Bot 🤖

The AI Interview Preparation Bot is an intelligent chatbot that simulates a real interview experience. It generates interview questions based on a selected role and evaluates the user's responses using LangChain and a Large Language Model (LLM).

## Features

- **Role-Based Question Generation:** Select from various roles like AI Engineer, Software Developer, Data Scientist, etc.
- **Mock Interview Simulation:** Answer questions step-by-step just like a real interview.
- **Answer Evaluation:** Get scores out of 10 based on Accuracy, Technical depth, Clarity, and Completeness.
- **Constructive Feedback:** Receive detailed feedback and suggestions for improvement.
- **Interview Performance Summary:** At the end of the session, review an aggregated report of your performance.

## Technologies Used

- Python
- Streamlit (Frontend interface)
- LangChain (LLM Application Framework)
- Ollama (Local Language Model execution)

## Getting Started

### 1. Clone the repository / Setup
Ensure you have Python 3.9+ installed.

### 2. Install Dependencies
Run the following command to install required packages:
```bash
pip install -r requirements.txt
```

### 3. Setup Ollama
You need to have Ollama installed and the `llama3.2:3b` model downloaded.
1. Install [Ollama](https://ollama.com/)
2. Open a terminal and run the following command to download the model:
```bash
ollama run llama3.2:3b
```

### 4. Run the Application
Start the Streamlit app locally by running:
```bash
streamlit run app.py
```

## 🐳 Deployment (Docker)

To deploy the application fully containerized (including Ollama and the AI model), you can use Docker.

1. Ensure you have Docker and Docker Compose installed.
2. Run the following command in the root directory:
```bash
docker-compose up -d --build
```
This will:
- Build the Streamlit application container.
- Start an Ollama backend server.
- Automatically download the `llama3.2:3b` model initially.

The app will be accessible at: `http://localhost:8501`.

## Future Improvements to Consider
- Voice-based interview simulation
- Integration with external Vector Databases (like Pinecone or FAISS) to draw from a static bank of established interview questions instead of purely synthetic questions.
