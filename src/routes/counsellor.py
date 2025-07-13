from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix='/counsellor', tags=["Admin"])

templates = Jinja2Templates(directory="templates", auto_reload=True)


# =====================================================
# SIGNUP USER
# =====================================================
@router.get("/dashboard", response_class=HTMLResponse)
def show_councellor_dashboard(request: Request):
     return templates.TemplateResponse("counsellor/dashboard.html", {"request": request})