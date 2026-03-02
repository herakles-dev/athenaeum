"""Alan Watts Library API - Semantic search and RAG chat."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import search, chat, browse, settings, info

app = FastAPI(
    title="Alan Watts Library",
    description="Vectorized knowledge base of Alan Watts' lectures and writings",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(browse.router, prefix="/api", tags=["browse"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(info.router, prefix="/api", tags=["info"])


@app.get("/health")
def health():
    return {"status": "healthy", "service": "alan-watts-library"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
