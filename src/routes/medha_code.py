from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.utils.auth_utils import auth_required

router    = APIRouter(prefix='/medha_code', tags=["Admin"])
templates = Jinja2Templates(directory="templates", auto_reload=True)

@router.get("/", response_class=HTMLResponse)
@auth_required(['student'])
async def show_new_lead_form(request: Request):
     return templates.TemplateResponse("students/medha_code.html", {"request": request})