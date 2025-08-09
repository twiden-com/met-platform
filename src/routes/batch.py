from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from supabase import AsyncClient
from src.config.database import get_db
from src.utils.auth_utils import auth_required
from typing import Optional
from datetime import date

router = APIRouter(prefix='/batches', tags=["Admin"])
templates = Jinja2Templates(directory="templates", auto_reload=True)


@router.get("/new", response_class=HTMLResponse)
@auth_required(['counsellor'])
async def show_new_batch_form(request: Request, db: AsyncClient = Depends(get_db)):
    result = await db.table('profiles').select('id, name').eq('role', 'trainer').execute()
    trainers = result.data
    return templates.TemplateResponse("batches/new_batch.html", {"request": request, "trainers": trainers})


@router.get("/", response_class=HTMLResponse)
@auth_required(['counsellor'])
async def show_all_batches(request: Request):
    return templates.TemplateResponse("batches/batch_list.html", {"request": request})

@router.get("/list/api", response_class=JSONResponse)
@auth_required(['counsellor'])
async def get_all_batches(request: Request, db: AsyncClient = Depends(get_db)):
    result = await db.table('batches').select('*').execute()
    return JSONResponse(content=result.data)


@router.post("/new")
@auth_required(['counsellor'])
async def create_batch(
    request: Request,
    batch_name: str = Form(...),
    start_date: date = Form(...),
    status: str = Form(...),
    trainer: str = Form(...),
    estimated_end_date: Optional[str] = Form(None),
    mode: Optional[str] = Form(None),
    class_time: Optional[str] = Form("Not Yet"),
    batch_campus: Optional[str] = Form(None),
    whatsapp_group_link: Optional[str] = Form(None),
    db: AsyncClient = Depends(get_db)
):
    try:
        # Get the current user's profile data from request state
        user_data = getattr(request.state, 'user_data', None)
        
        # Get profile_id from the user's profile data
        profile_id = user_data.profile.get('id')
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile ID not found")
        
        # Prepare batch data
        batch_data = {
            "profile_id": profile_id,
            "batch_name": batch_name,
            "start_date": start_date.isoformat(),
            "status": status,
            "trainer": trainer,
            "class_time": class_time if class_time else "Not Yet"
        }
        
        # Handle estimated_end_date - only add if not empty
        if estimated_end_date and estimated_end_date.strip():
            try:
                # Parse the date string and convert to ISO format
                from datetime import datetime
                parsed_date = datetime.strptime(estimated_end_date.strip(), "%Y-%m-%d").date()
                batch_data["estimated_end_date"] = parsed_date.isoformat()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid estimated end date format")
        
        # Add other optional fields if provided
        if mode and mode.strip():
            batch_data["mode"] = mode.strip()
        if batch_campus and batch_campus.strip():
            batch_data["batch_campus"] = batch_campus.strip()
        if whatsapp_group_link and whatsapp_group_link.strip():
            batch_data["whatsapp_group_link"] = whatsapp_group_link.strip()
        
        # Insert into database
        result = await db.table('batches').insert(batch_data).execute()
        
        if result.data:
            # Return success response
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "Batch created successfully",
                    "data": result.data[0]
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create batch")
            
    except Exception as e:
        print(f"Error creating batch: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error creating batch: {str(e)}"
            }
        )