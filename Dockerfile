FROM ollama/ollama:latest

# Environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/venv \
    PATH="/app/venv/bin:$PATH"

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3.12-venv \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /app/venv

# Install Python dependencies in venv
RUN /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Pre-download model during build
RUN ollama serve & \
    sleep 10 && \
    ollama pull gpt-oss:120b


