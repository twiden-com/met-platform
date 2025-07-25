from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.utils.auth_utils import auth_required

router    = APIRouter(prefix='/counsellor', tags=["Admin"])
templates = Jinja2Templates(directory="templates", auto_reload=True)


# =====================================================
# SIGNUP USER
# =====================================================
@router.get("/dashboard", response_class=HTMLResponse)
@auth_required(['counsellor'])
async def show_councellor_dashboard(request: Request):
     profile = request.state.user_data.profile
     return templates.TemplateResponse("counsellor/dashboard.html", {"request": request, "profile":profile})

@router.get("/new-enquiry", response_class=HTMLResponse)
@auth_required(['counsellor'])
async def show_new_enquiry_form(request: Request):
     return templates.TemplateResponse("counsellor/new_enquiry.html", {"request": request})

