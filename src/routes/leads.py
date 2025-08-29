from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.utils.auth_utils import auth_required

router    = APIRouter(prefix='/leads', tags=["Leads"])
templates = Jinja2Templates(directory="templates", auto_reload=True)

@router.get("/new", response_class=HTMLResponse)
@auth_required(['counsellor'])
async def show_new_lead_form(request: Request):
     return templates.TemplateResponse("leads/new_lead.html", {"request": request})

@router.get("/", response_class=HTMLResponse)
@auth_required(['counsellor'])
async def show_lead_list(request: Request):
     return templates.TemplateResponse("leads/lead_list.html", {"request": request})