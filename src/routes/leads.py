from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from src.external.bland import bland_trigger_demo_call
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

@router.post("/call", response_class=HTMLResponse)
async def trigger_ai_call_to_lead(request: Request):
     details = await request.json()
     bland_trigger_demo_call(details['user_name'], details['user_phone'])
     return JSONResponse(status_code=200)
