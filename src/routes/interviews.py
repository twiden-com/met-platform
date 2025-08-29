from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from supabase import AsyncClient
from src.external.bland import bland_start_interview, call_status
from src.utils.auth_utils import auth_required
from src.config.database import get_db 

router    = APIRouter(prefix='/interviews', tags=["Admin"])
templates = Jinja2Templates(directory="templates", auto_reload=True)



@router.get("/", response_class=HTMLResponse)
# @auth_required(['student'])
async def show_interviews(request: Request, db: AsyncClient = Depends(get_db)):
    result = await db.table("interview_templates").select('*').execute()
    if result.data:
      return templates.TemplateResponse("/interviews/interview_list.html", {'request': request, 'interviews': result.data})

@router.get("/start/{interview_id}", response_class=HTMLResponse)
@auth_required(['student'] )
async def start_interview(request: Request, interview_id: int, db: AsyncClient = Depends(get_db)):
     profile = request.state.user_data.profile
     phone = profile['phone_number']
     phone = phone.split('-')[1]
     result = await db.table('interview_templates').select("*").eq('id', interview_id).execute()

     if result.data:
         interview = result.data[0]
         res = bland_start_interview(
            profile_id=profile['id'],
            course_name= interview['course_name'],
            interview_id= interview['id'],
            interview_topic=interview['interview_topic'],
            interview_max_duration=interview['interview_max_duration'],
            interview_questions=interview['interview_questions'],
            trainer_name=interview['trainer_name'],
            user_name=profile['name'],
            phone_number=phone
         )
         return templates.TemplateResponse("interviews/interview_room.html", {"request": request, 'interview_details': result.data[0], 'call_id': res['call_id']})
     

@router.get("/{call_id}/status", response_class=JSONResponse)
async def interview_status(request: Request, call_id: str):
   res = call_status(call_id=call_id)
   return JSONResponse({
           'completed': res['completed'],
           'queue_status': res['queue_status']
       })


@router.get("/{call_id}/result", response_class=JSONResponse)
async def interview_result(request: Request, call_id: str):
   res = call_status(call_id=call_id)
   return templates.TemplateResponse("/interviews/interview_result.html", {'request': request, 'interview_result': res})
    