# CaRMS Program Explorer

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Dagster](https://img.shields.io/badge/Dagster-1.9-purple.svg)](https://dagster.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)
[![Terraform](https://img.shields.io/badge/Terraform-AWS-7B42BC.svg)](https://www.terraform.io)

An AI-powered platform for discovering Canadian medical residency programs. Built with the CaRMS tech stack: **PostgreSQL + pgvector**, **SQLModel/SQLAlchemy**, **Dagster**, **FastAPI**, **Claude Agent SDK**, and **Streamlit**.

## Architecture

```
Raw Data (Excel/CSV/JSON)
    │
    ▼
Dagster ETL ──→ PostgreSQL + pgvector
                     │
            ┌────────┼────────────┐
            ▼        ▼            ▼
       FastAPI    Streamlit    Claude Agent SDK
     (REST API)  (Analytics)   (AI Chat Agent)
         │                         │
         └────── Web Chat UI ──────┘
                     │
              Docker Compose / Terraform ECS
```

## Features

| Feature | Description | Requires API Key |
|---------|-------------|:---:|
| **REST API** | Full CRUD + semantic search over 815 programs | No |
| **Semantic Search** | Natural language search via all-MiniLM-L6-v2 + pgvector | No |
| **Analytics Dashboard** | Interactive Streamlit charts and program explorer | No |
| **AI Chat Agent** | Conversational program discovery with Claude Agent SDK | Yes |
| **ETL Pipeline** | Dagster-orchestrated data ingestion with asset lineage | No |

## Quickstart

```bash
# Clone
git clone https://github.com/your-repo/carms-explorer.git
cd carms-explorer

# Configure (optionally add ANTHROPIC_API_KEY for AI chat)
cp .env.example .env

# Launch all services
docker compose -f docker/docker-compose.yml up -d

# Run ETL: Open http://localhost:3000 → Assets → Materialize All
# Then explore:
#   http://localhost:8000       → Chat UI + API
#   http://localhost:8000/docs  → Swagger API docs
#   http://localhost:8501       → Analytics dashboard
#   http://localhost:8080       → Documentation
```

## Data

Built on public CaRMS residency program data from the [Junior-Data-Scientist](https://github.com/dnokes/Junior-Data-Scientist) repository:

- **37** medical disciplines
- **815** residency programs across **17** Canadian medical schools
- Full program descriptions with 15 structured sections
- ~8,000+ semantic embedding chunks for retrieval

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Database | PostgreSQL 16 + pgvector (HNSW cosine index) |
| ORM | SQLModel / SQLAlchemy 2.0 |
| ETL | Dagster (asset-based, Postgres-backed metadata) |
| API | FastAPI + Pydantic v2 |
| Search | all-MiniLM-L6-v2 (384d, local, no API key) |
| AI Agent | Claude Agent SDK with custom MCP tools |
| Dashboard | Streamlit + Plotly |
| Containers | Docker Compose (7 services) |
| Cloud | Terraform → AWS ECS Fargate + RDS + ALB + S3 |
| Docs | MkDocs Material with Mermaid diagrams |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/disciplines/` | List disciplines with program counts |
| GET | `/programs/` | List/filter programs |
| GET | `/programs/{id}` | Program detail with description |
| POST | `/search/` | Semantic search |
| GET | `/analytics/overview` | Aggregate statistics |
| GET | `/analytics/disciplines` | By-discipline breakdown |
| GET | `/analytics/schools` | By-school breakdown |
| POST | `/agent/chat` | AI agent chat (SSE streaming) |

## Project Structure

```
├── src/carms/
│   ├── config.py              # Pydantic Settings
│   ├── db/
│   │   ├── engine.py          # SQLAlchemy engine
│   │   └── models.py          # SQLModel tables (5 tables)
│   ├── etl/
│   │   ├── resources.py       # Database + Embedding resources
│   │   ├── assets/            # Dagster assets (raw → staging → embeddings)
│   │   └── definitions.py     # Dagster Definitions
│   ├── api/
│   │   ├── main.py            # FastAPI app factory
│   │   ├── schemas.py         # Pydantic models
│   │   ├── routers/           # Endpoint handlers
│   │   └── static/            # Chat UI (HTML/CSS/JS)
│   ├── search/
│   │   ├── embeddings.py      # Model management
│   │   └── retriever.py       # SearchService (pgvector queries)
│   ├── agent/
│   │   ├── tools.py           # 7 MCP tools for program exploration
│   │   └── agent.py           # ClaudeSDKClient configuration
│   └── dashboard/
│       └── app.py             # Streamlit analytics app
├── docker/                    # Dockerfiles + docker-compose.yml
├── terraform/                 # AWS infrastructure (ECS, RDS, ALB, S3)
├── tests/                     # pytest test suite
├── docs/                      # MkDocs Material documentation
└── data/raw/                  # Source data files
```

## Development

```bash
# Install all dependencies
make install

# Run API locally
make dev

# Run Streamlit locally
make dashboard

# Run tests
make test

# Lint and format
make lint
make format
```

## AWS Deployment

```bash
cd terraform
terraform init
terraform plan -var="db_password=your-secure-password"
terraform apply -var="db_password=your-secure-password"
```

See [Deployment docs](docs/docs/deployment.md) for full instructions.

## License

MIT
