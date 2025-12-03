from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def health():
    """Проверяет работу сервера."""
    return {"status": "ok"}
