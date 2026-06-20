from fastapi import APIRouter  # type: ignore[import]

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "ok"
    }