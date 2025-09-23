from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from supabase import AsyncClient
from src.external.bland import bland_start_interview, call_status
from src.utils.auth_utils import auth_required
from src.config.database import get_db 
import pytz
router    = APIRouter(prefix='/interviews', tags=["Interviews"])
templates = Jinja2Templates(directory="templates", auto_reload=True)

# Add custom filter
def format_ist(value: str):
    try:
        # Parse the string from Supabase
        dt = datetime.fromisoformat(value.replace(" ", "T"))  
        # Convert UTC → IST
        ist = dt.astimezone(pytz.timezone("Asia/Kolkata"))
        return ist.strftime("%d-%m-%Y %I:%M %p")  # ex: 29-08-2025 01:08 PM
    except Exception:
        return value  # fallback if parsing fails

templates.env.filters["isttime"] = format_ist

@router.get("/", response_class=HTMLResponse)
@auth_required(['student'])
async def show_interviews(request: Request, db: AsyncClient = Depends(get_db)):
    profile = request.state.user_data.profile
    result = await db.table("interview_templates").select('*').execute()
    result1 = await db.table('interview_results').select("*").eq('profile_id', profile['id']).execute()
    
    total_seconds = sum(d["duration"] for d in result1.data)
    minutes, seconds = divmod(total_seconds, 60)  # split into mins & secs
    readable_time = f"{minutes}m {seconds}s"
    stats = {
       'available': len(result.data),
       'completed': len(result1.data),
       'avg_score': sum(d["score"] for d in result1.data) / len(result1.data),
       'duration': readable_time
    }
    if result.data and result1.data:
      return templates.TemplateResponse("/interviews/interview_list.html", {'request': request, 'interviews': result.data, 'stats': stats, 'interview_results': result1.data})

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


@router.get("/{call_id}/save", response_class=JSONResponse)
@auth_required(['student'] )
async def save_interview_result(request: Request, call_id: str, db: AsyncClient = Depends(get_db)):
   profile = request.state.user_data.profile
   res = call_status(call_id=call_id)
   result = await db.table('interview_results').insert({
      'profile_id': profile['id'],
      'interview_id': res['variables']['metadata']['interview_id'],
      'call_id': call_id,
      'score': res['analysis']['overall_score_out_of_10'],
      'topic': res['variables']['metadata']['interview_topic'],
      'duration': res['corrected_duration'],
      'cost': res['price'],
      'course_name': res['variables']['metadata']['course_name'],
   }).execute()
   if result.data:
      return JSONResponse({
         "success": True
      })
   
@router.get("/{call_id}/result", response_class=JSONResponse)
async def interview_result(request: Request, call_id: str):
   res = call_status(call_id=call_id)
   return templates.TemplateResponse("/interviews/interview_result.html", {'request': request, 'interview_result': res})
    

