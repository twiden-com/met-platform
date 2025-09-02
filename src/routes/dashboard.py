from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from supabase import AsyncClient
from src.config.database import get_db
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

@router.get("/switch")
@auth_required(['counsellor', 'admin', 'student', 'trainer'])
async def switch_role(request: Request, role, db: AsyncClient = Depends(get_db)):
     profile = request.state.user_data.profile
     res = await db.table('profiles').update({
          'role': role
     }).eq('id', profile['id']).execute()
     if res.data:
     #    base_url = str(request.base_url).replace('http://', 'https://')
     #    redirect_url = f"{base_url}dashboard"
     #    return RedirectResponse(redirect_url, status_code=302)
          return JSONResponse({'message': 'success'}, status_code=200)
