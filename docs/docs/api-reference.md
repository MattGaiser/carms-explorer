# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

## Endpoints

### Health
- `GET /health` - Check API and database health

### Disciplines
- `GET /disciplines/` - List all 37 disciplines with program counts

### Programs
- `GET /programs/` - List programs with optional filters
    - `?discipline_id=13` - Filter by discipline
    - `?school_id=1` - Filter by school
    - `?site=Toronto` - Filter by site (partial match)
    - `?q=family` - Text search in program name
    - `?limit=50&offset=0` - Pagination
- `GET /programs/{id}` - Get program detail with full description

### Search
- `POST /search/` - Semantic search over program descriptions
    ```json
    {
        "query": "rural family medicine with research focus",
        "top_k": 10,
        "discipline_id": null,
        "school_id": null,
        "site": null
    }
    ```

### Analytics
- `GET /analytics/overview` - Aggregate counts (programs, disciplines, schools, embeddings)
- `GET /analytics/disciplines` - Program counts per discipline
- `GET /analytics/schools` - Program counts per school

### Agent (requires ANTHROPIC_API_KEY)
- `GET /agent/status` - Check if AI agent is available
- `POST /agent/chat` - Chat with AI agent (SSE streaming)
    ```json
    {
        "message": "Find me family medicine programs in Ontario",
        "session_id": "optional-session-id"
    }
    ```
- `DELETE /agent/session/{session_id}` - Clean up a chat session
