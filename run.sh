#!/bin/bash

# Start Ollama service in the background
echo "Starting Ollama server..."
ollama serve &

# Wait for Ollama to be available
echo "Waiting for Ollama to initialize..."
sleep 5

# Pull the model
echo "Pulling llama3.2:3b model..."
ollama pull llama3.2:3b

# Start FastAPI server on port 7860
echo "Starting FastAPI server..."
uvicorn server:app --host 0.0.0.0 --port 7860
