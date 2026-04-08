FROM python:3.9-slim

# Install curl and zstd to download and extract Ollama
RUN apt-get update && apt-get install -y curl zstd && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set up a new user named "user" with user ID 1000 for Hugging Face compatibility
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    OLLAMA_MODELS=/home/user/.ollama/models

# Set the working directory
WORKDIR $HOME/app

# Copy requirements and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else
COPY --chown=user . .

# Make the run script executable
RUN chmod +x run.sh

# Expose the mandatory Hugging Face port
EXPOSE 7860

# Run the startup script
CMD ["./run.sh"]
