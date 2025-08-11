from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.utils.auth_utils import auth_required

router    = APIRouter(prefix='/dashboard', tags=["Admin"])
templates = Jinja2Templates(directory="templates", auto_reload=True)

# =====================================================
# SIGNUP USER
# =====================================================
@router.get("/", response_class=HTMLResponse)
@auth_required(['counsellor', 'admin', 'trainer', 'student'])
async def show_dashboard(request: Request):
     profile = request.state.user_data.profile
     if profile.get('role')   == 'counsellor':
          return templates.TemplateResponse("dashboards/counsellor.html", {"request": request, "profile":profile})
     elif profile.get('role') == 'student':
          return templates.TemplateResponse("dashboards/student.html", {"request": request, "profile":profile})
     elif profile.get('role') == 'trainer':
          return templates.TemplateResponse("dashboards/trainer.html", {"request": request, "profile":profile})
     elif profile.get('role') == 'admin':
          return templates.TemplateResponse("dashboards/admin.html", {"request": request, "profile":profile})

