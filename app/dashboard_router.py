from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

PAGES_DIR = Path(__file__).resolve().parent / "pages"

router = APIRouter(prefix="/dashboard")

@router.get("/", response_class=HTMLResponse)
async def dashboard_page():
    return (PAGES_DIR / "dashboard.html").read_text()