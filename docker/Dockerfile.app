FROM python:3.12-slim AS base

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Claude Agent SDK
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI (needed by claude-agent-sdk)
RUN npm install -g @anthropic-ai/claude-code

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir ".[api,agent,rag]"


COPY src/ ./src/
COPY data/raw/ ./data/raw/

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uvicorn", "carms.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
