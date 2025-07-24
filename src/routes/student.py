from functools import wraps
from inspect import iscoroutinefunction
from fastapi import APIRouter, Depends, Form, status, HTTPException,Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from src.config.database import get_admin_db, get_db
from supabase import Client, AsyncClient
from src.external.messagecentral import send_otp, verify_otp
import json
from typing import Optional, List, Callable, Any
from src.utils.auth_utils import auth_required


router = APIRouter(prefix="/student", tags=["Student"])


@router.post("/create/skip_otp")
@auth_required(['counsellor'])
async def student_skip_otp(request:Request, country_code:str, phone: str, db:AsyncClient = Depends(get_db)): #Eg. country_code - 91, phone - 7013908751 
    try:
        db_phone = country_code + '-' + phone
        profile = await db.table('profiles').select("*").eq('phone_number', db_phone.strip()).execute()
        if len(profile.data) > 0:
            if profile.data[0].get('is_active') == 1:
                return JSONResponse(
                    status_code=200,
                    content={    
                    "message": 'EXISTING_USER',
                    "redirectUrl": f"/{request.state.user_data.profile.get('role')}/students?id={profile.data[0].get('user_id')}"
                })
            elif profile.data[0].get('is_active') == 0:
                response = JSONResponse(
                    content={
                        "success": True
                    }
                )
                return response
        
        email = password = country_code + '-' + phone + "@met.com"

        result = await db.auth.sign_up(
                    {
                        "email"   : email,
                        "password": password,
                    }
        )

        profile = await db.table("profiles").insert({
                    "user_id"       : result.user.id,
                    "is_verified": 3, #3 is for Auto Confirm
                    "is_active": 0,
                    "phone_number": country_code + '-' + phone
        }).execute()

        # Create JSONResponse
        response = JSONResponse(
                    content={
                        "success": True
                    }
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="Lead Creation Failed")

@router.post("/send/phone_otp")
@auth_required(['counsellor'])
async def student_send_otp(request:Request, country_code:str, phone: str, db:AsyncClient = Depends(get_db)): #Eg. country_code - 91, phone - 7013908751 
    try:
        db_phone = country_code + '-' + phone
        profile = await db.table('profiles').select("*").eq('phone_number', db_phone.strip()).execute()
        if profile.data and len(profile.data) > 0:
            return JSONResponse(
                status_code=200,
                content={    
                "message": 'EXISTING_USER',
                "redirectUrl": f"/{request.state.user_data.profile.get('role')}/students?id={profile.data[0].get('user_id')}"
            })

        res = send_otp(country_code=country_code, phone=phone)
        data =  json.loads(res.text)
        return JSONResponse(status_code=200, content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@router.post("/verify/phone_otp")
async def student_validate_otp(phone:str, country_code:str, otp: str, verification_id: str, db:AsyncClient = Depends(get_db)): #Eg. otp - 287976 
    try:
        res = verify_otp(code=otp, verification_id=verification_id, country_code=country_code, phone=phone)
        
        if res.status_code == 200:
            
            data = json.loads(res.text)
            
            if data.get("message") == 'VERIFICATION_EXPIRED':
                return data
            
            elif data.get("message") == 'SUCCESS':
                
                email = password = country_code + '-' + phone + "@met.com"
                
                result = await db.auth.sign_up(
                    {
                        "email"   : email,
                        "password": password,
                    }
                )

                profile = await db.table("profiles").insert({
                    "user_id"       : result.user.id,
                    "is_verified": 1,
                    "is_active": 0,
                    "phone_number": country_code + '-' + phone
                }).execute()

                # Create JSONResponse
                response = JSONResponse(
                    content={
                        "success": True
                    }
                )

                return response

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to verify OTP")
    

@router.post("/new_enquiry/submit")
@auth_required(['counsellor', 'admin'])
async def create_student_enquiry(
    request: Request,
    verified_phone: str = Form(...),
    verification_id: Optional[str] = Form(None),
    student_name: str = Form(...),
    additional_members: Optional[int] = Form(0),
    location: Optional[str] = Form(None),
    mode: Optional[str] = Form(None),
    degree: Optional[str] = Form(None),
    purpose: Optional[str] = Form(None),
    slot_preference: Optional[str] = Form(None),
    lead_source: Optional[str] = Form(None),
    counselled_by: Optional[str] = Form(None),
    urgency: Optional[str] = Form(None),
    interested_courses: List[str] = Form(...),
    comments: Optional[str] = Form(None),
    send_brochure: Optional[bool] = Form(False),
    db: AsyncClient = Depends(get_db)
):
    """
    Create a new student enquiry profile
    """
    try:
        # Validate required fields
        if not student_name.strip():
            raise HTTPException(status_code=400, detail="Student name is required")
        
        if not interested_courses:
            raise HTTPException(status_code=400, detail="At least one interested course must be selected")
        
        # Check if phone number already exists
        existing_profile = await db.table('profiles').select("*").eq('phone_number', verified_phone).execute()
        
        if existing_profile.data and len(existing_profile.data) > 0:
            raise HTTPException(
                status_code=400, 
                detail="A profile with this phone number already exists"
            )
        
        # Get counsellor info from request state
        counsellor_id = request.state.user_data.user.id if hasattr(request.state, 'user_data') else None
        
        # Prepare profile data
        profile_data = {
            "phone_number": verified_phone,
            "verification_id": verification_id,
            "student_name": student_name.strip(),
            "additional_members": additional_members or 0,
            "location": location.strip() if location else None,
            "mode": mode,
            "degree": degree,
            "purpose": purpose,
            "slot_preference": slot_preference,
            "lead_source": lead_source,
            "counselled_by": counselled_by,
            "urgency": urgency,
            "interested_courses": json.dumps(interested_courses),
            "comments": comments.strip() if comments else None,
            "send_brochure": bool(send_brochure),
            "created_by": counsellor_id,
            "is_verified": 1,
            "created_at": "now()",
            "updated_at": "now()"
        }
        
        # Insert into database
        result = await db.table('profiles').insert(profile_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create profile")
        
        # Return success response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Student enquiry created successfully",
                "profile_id": result.data[0].get('id') if result.data else None
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Error creating student enquiry: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create student enquiry")