from fastapi import APIRouter, Depends

from app.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    return {"status": "ok"}


@router.get("/db")
def db_health_check(db=Depends(get_db)):
    cursor = db.execute("SELECT 1 AS status")
    result = cursor.fetchone()
    if result["status"] == 1:
        return {"status": "ok"}
    return {"status": "error"}
