# CaRMS Program Explorer

An AI-powered platform for discovering Canadian medical residency programs.

## Features

- **REST API** with semantic search over 815 program descriptions
- **AI Chat Agent** powered by the Claude Agent SDK for conversational program exploration
- **Analytics Dashboard** built with Streamlit for visual program landscape analysis
- **ETL Pipeline** orchestrated by Dagster for data ingestion and transformation

## Quickstart

```bash
# Clone and setup
git clone https://github.com/your-repo/carms-explorer.git
cd carms-explorer
cp .env.example .env

# Optionally add your Anthropic API key for AI chat
# echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Start all services
docker compose -f docker/docker-compose.yml up -d

# Open Dagster UI and materialize all assets
open http://localhost:3000

# Explore
open http://localhost:8000       # Chat UI + API
open http://localhost:8000/docs  # Swagger API docs
open http://localhost:8501       # Analytics dashboard
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL 16 + pgvector |
| ORM | SQLModel / SQLAlchemy |
| ETL | Dagster |
| API | FastAPI |
| Search | all-MiniLM-L6-v2 + pgvector cosine similarity |
| AI Agent | Claude Agent SDK |
| Dashboard | Streamlit + Plotly |
| Infrastructure | Docker Compose / Terraform (AWS ECS) |
| Documentation | MkDocs Material |
