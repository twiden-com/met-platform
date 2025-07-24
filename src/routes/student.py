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
    
from fastapi import Request, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Optional, List, Dict, Any

@router.post("/new_enquiry/submit")
@auth_required(['counsellor', 'admin'])
async def create_student_enquiry(
    request: Request,
    db: AsyncClient = Depends(get_db)
):
    """Create a new student enquiry profile"""
    try:
        # Get form data manually to handle validation properly
        form_data = await request.form()
        
        # Convert form data to dict, handling special cases
        data_dict = {}
        for key, value in form_data.items():
            if key == 'interested_courses':
                # Handle multiple values for checkboxes
                if isinstance(value, list):
                    data_dict[key] = value
                else:
                    # If single value, get all values for this key
                    data_dict[key] = form_data.getlist(key)
            elif key in ['additional_people', 'passout_year']:
                # Handle integer fields - convert empty strings to None
                data_dict[key] = int(value) if value != '' else None
            elif key == 'send_brochure':
                # Handle boolean fields
                data_dict[key] = value == 'true' if isinstance(value, str) else bool(value)
            else:
                # Handle string fields - convert empty strings to None for optional fields
                data_dict[key] = value if value != '' else None
        
        # Create Pydantic model for validation with our custom error handling
        try:
            enquiry_data = StudentEnquiryRequest(**data_dict)
        except ValidationError as e:
            # Custom Pydantic validation error formatting
            error_messages = []
            error_fields = []  # Track which fields have errors
            
            for error in e.errors():
                field_name = error['loc'][0] if error['loc'] else 'unknown'
                error_fields.append(field_name)  # Add to error fields list
                
                # Convert field name to readable format
                field_display_names = {
                    'verified_phone': 'Phone Number',
                    'student_name': 'Student Name',
                    'additional_people': 'Additional People',
                    'college_name': 'College Name',
                    'passout_year': 'Year of Passout',
                    'lead_source': 'Lead Source',
                    'slot_preference': 'Slot Preference',
                    'counselled_by': 'Counselled By',
                    'interested_courses': 'Interested Courses'
                }
                
                readable_field = field_display_names.get(field_name, field_name.replace('_', ' ').title())
                message = error['msg']
                
                # Clean up common pydantic error messages
                if 'field required' in message.lower():
                    message = "is required"
                elif 'ensure this value has at least' in message.lower():
                    message = "is required"
                elif 'ensure this value is greater than or equal to' in message.lower():
                    message = "must be a valid number (minimum value applies)"
                elif 'ensure this value is less than or equal to' in message.lower():
                    message = "exceeds maximum allowed value"
                elif 'input should be a valid integer' in message.lower():
                    message = "must be a valid year (numbers only)"
                elif 'string too short' in message.lower():
                    message = "is too short"
                elif 'string too long' in message.lower():
                    message = "is too long"
                elif 'invalid' in message.lower() and 'course' in message.lower():
                    message = "contains invalid course selection"
                
                error_messages.append(f"• {readable_field}: {message}")
            
            formatted_message = "Please fix the following errors:\n\n" + "\n".join(error_messages)
            
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": formatted_message,
                    "error_fields": error_fields,  # Include field names for frontend highlighting
                    "error_type": "validation"
                }
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
        
    except Exception as e:
        print(f"Error creating enquiry: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to create student enquiry. Please try again."
            }
        )