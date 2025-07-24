from functools import wraps
from inspect import iscoroutinefunction
from fastapi import APIRouter, Depends, Form, status, HTTPException,Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, ValidationError
from src.config.database import get_admin_db, get_db
from supabase import Client, AsyncClient
from src.external.messagecentral import send_otp, verify_otp
import json
from typing import Optional, List, Callable, Any
from src.schemas.new_enquiry_schema import StudentEnquiryRequest
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
    additional_people: Optional[int] = Form(0),
    country: Optional[str] = Form("India"),
    state: Optional[str] = Form(None),
    place: Optional[str] = Form(None),
    purpose: Optional[str] = Form(None),
    college_name: Optional[str] = Form(None),
    passout_year: Optional[int] = Form(None),
    degree: Optional[str] = Form(None),
    lead_source: Optional[str] = Form(None),
    mode: Optional[str] = Form(None),
    slot_preference: Optional[str] = Form(None),
    counselled_by: Optional[str] = Form(None),
    urgency: Optional[str] = Form(None),
    interested_courses: List[str] = Form(...),
    comments: Optional[str] = Form(None),
    send_brochure: Optional[bool] = Form(False),
    db: AsyncClient = Depends(get_db)
):
    """Create a new student enquiry profile"""
    try:
        # Create Pydantic model for validation
        enquiry_data = StudentEnquiryRequest(
            verified_phone=verified_phone,
            verification_id=verification_id,
            student_name=student_name,
            additional_people=additional_people,
            country=country,
            state=state,
            place=place,
            purpose=purpose,
            college_name=college_name,
            passout_year=passout_year,
            degree=degree,
            lead_source=lead_source,
            mode=mode,
            slot_preference=slot_preference,
            counselled_by=counselled_by,
            urgency=urgency,
            interested_courses=interested_courses,
            comments=comments,
            send_brochure=send_brochure
        )
        
        # Check if phone already exists
        existing = await db.table('profiles').select("user_id, student_name").eq('phone_number', enquiry_data.verified_phone).execute()
        
        # Get counsellor ID
        counsellor_id = getattr(request.state.user_data.user, 'id', None) if hasattr(request.state, 'user_data') else None
        
        # Convert to database format
        profile_data = enquiry_data.to_db_dict(counsellor_id)
        
        if existing.data:
            # Update existing profile
            result = await db.table('profiles').update(profile_data).eq('user_id', existing.data[0]['user_id']).execute()
            action = "updated"
        else:
            # Insert new profile
            result = await db.table('profiles').insert(profile_data).execute()
            action = "created"
        
        if not result.data:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Failed to save profile"
                }
            )
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Student enquiry for {enquiry_data.student_name} {action} successfully!",
                "user_id": result.data[0].get('user_id'),
                "profile_id": result.data[0].get('id')
            }
        )
        
    except ValidationError as e:
        # Pydantic validation errors
        error_messages = []
        for error in e.errors():
            field = error['loc'][0] if error['loc'] else 'unknown'
            message = error['msg']
            error_messages.append(f"{field}: {message}")
        
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": f"Validation failed: {'; '.join(error_messages)}"
            }
        )
        
    except HTTPException as he:
        return JSONResponse(
            status_code=he.status_code,
            content={
                "success": False,
                "message": he.detail
            }
        )
        
    except Exception as e:
        print(f"Error creating enquiry: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to create student enquiry"
            }
        )