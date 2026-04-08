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

# Start Streamlit on port 7860
echo "Starting Streamlit..."
streamlit run app.py --server.port 7860 --server.address 0.0.0.0
