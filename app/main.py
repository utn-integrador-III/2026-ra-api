from fastapi import FastAPI  # type: ignore[import]
from app.api.v1.routes.health import router as health_router

app = FastAPI(
    title="PathAR API",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "PathAR API is running"}

app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"]
)