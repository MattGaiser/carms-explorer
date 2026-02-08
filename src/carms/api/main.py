"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from carms.api.routers import analytics, disciplines, health, programs, reports, search

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load embedding model on startup."""
    try:
        from carms.search.embeddings import get_embedding_model

        get_embedding_model()
    except Exception:
        pass  # Model loading is optional at startup
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CaRMS Program Explorer",
        description="AI-powered Canadian medical residency program discovery platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core routers
    app.include_router(health.router)
    app.include_router(disciplines.router)
    app.include_router(programs.router)
    app.include_router(search.router)
    app.include_router(analytics.router)
    app.include_router(reports.router)

    # RAG router (optional, requires langchain + anthropic key)
    try:
        from carms.api.routers.rag import router as rag_router

        app.include_router(rag_router)
    except ImportError:
        pass

    # Agent router (optional, requires anthropic key)
    try:
        from carms.api.routers.agent import router as agent_router

        app.include_router(agent_router)
    except ImportError:
        pass

    # Static files for chat UI
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        """Serve the chat UI."""
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"message": "CaRMS Program Explorer API", "docs": "/docs"}

    return app


app = create_app()
