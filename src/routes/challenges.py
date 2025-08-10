
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from supabase import AsyncClient
from src.config.database import get_db
from src.utils.auth_utils import auth_required

router    = APIRouter(prefix='/challenges', tags=["Admin"])
templates = Jinja2Templates(directory="templates", auto_reload=True)


@router.get("/", response_class=HTMLResponse)
@auth_required(['student'])
async def get_challenegs(request: Request, db:AsyncClient = Depends(get_db)):
     result = await db.table('challenges').select('*').eq('course', 'python_full_stack').execute()
     return templates.TemplateResponse("leads/new_lead.html", {"request": request, 'challenges': result.data})


@router.get("/api/challenges", response_class=JSONResponse)
@auth_required(['student'])
async def get_challenges_api(
    request: Request, 
    course: Optional[str] = Query(None, description="Filter by course"),
    db: AsyncClient = Depends(get_db)
):
    """API endpoint to fetch challenges by course"""
    try:
        query = db.table('challenges').select('*')
        
        if course:
            # Convert frontend course names to database course names
            course_mapping = {
                'python_full_stack': 'python_full_stack',
                'java_fullstack': 'java_fullstack', 
                'digital_marketing': 'digital_marketing',
                'cybersecurity': 'cybersecurity',
                'data_science': 'data_science',
                'data_analytics': 'data_analytics'
            }
            
            db_course = course_mapping.get(course, course)
            query = query.eq('course', db_course)
        
        result = await query.execute()
        
        if result.data:
            return {"success": True, "data": result.data}
        else:
            return {"success": True, "data": []}
            
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}

@router.get("/api/challenge/{challenge_id}")
@auth_required(['student'])
async def get_challenge_by_id(
    challenge_id: int,
    request: Request,
    db: AsyncClient = Depends(get_db)
):
    """Get a specific challenge by ID"""
    try:
        result = await db.table('challenges').select('*').eq('id', challenge_id).execute()
        
        if result.data:
            return {"success": True, "data": result.data[0]}
        else:
            return {"success": False, "error": "Challenge not found", "data": None}
            
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}