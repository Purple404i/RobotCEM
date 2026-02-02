from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_route():
    return {"message": "Routes working"}
