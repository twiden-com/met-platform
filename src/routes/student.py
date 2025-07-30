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
@auth_required(['counsellor'], signup_flow=True)
async def student_skip_otp(request:Request, country_code:str, phone: str, db:AsyncClient = Depends(get_db)): #Eg. country_code - 91, phone - 7013908751 
    try:
        db_phone = country_code + '-' + phone
        profile = await db.table('profiles').select("*").eq('phone_number', db_phone.strip()).execute()
        if len(profile.data) > 0:
                return JSONResponse(
                    status_code=200,
                    content={    
                    "message": 'EXISTING_USER',
                    "redirectUrl": f"/{request.state.user_data.profile.get('role')}/student/leads?id={profile.data[0].get('user_id')}"
                })
        
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
                    "role": 'student',
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
@auth_required([], signup_flow=True)
async def student_validate_otp(request:Request, phone:str, country_code:str, otp: str, verification_id: str, db:AsyncClient = Depends(get_db)): #Eg. otp - 287976 
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
@auth_required(['counsellor'])
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
                    'name': 'Student Name',
                    'additional_people': 'Additional People',
                    'college_name': 'College Name',
                    'passout_year': 'Year of Passout',
                    'lead_source': 'Lead Source',
                    'slot_preference': 'Slot Preference',
                    'counselled_by': 'Counselled By',
                    'interested_courses': 'Interested Courses',
                    'lead_quality': 'Lead Quality',
                    'fee_quoted': 'Fee Quoted'
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
        existing = await db.table('profiles').select("user_id, name").eq('phone_number', enquiry_data.verified_phone).execute()
        
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
                "message": f"Student enquiry for {enquiry_data.name} {action} successfully!",
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
    
# Add this to your students.py router file
from typing import Optional, List
from fastapi import Query
import json

from typing import Optional, List
from fastapi import Query
import json

@router.get("/leads")
@auth_required(['counsellor', 'admin'])
async def get_student_leads(
    request: Request,
    db: AsyncClient = Depends(get_db),
    
    # Filters - matching frontend field names
    counsellor: Optional[str] = Query(None, description="Comma-separated counsellor values"),
    lead_source: Optional[str] = Query(None, description="Comma-separated lead source values"),
    slot_preference: Optional[str] = Query(None, description="Comma-separated slot preference values"),
    course: Optional[str] = Query(None, description="Single course name from dropdown"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    followupdate_start: Optional[str] = Query(None, description="Follow-up start date (YYYY-MM-DD)"),
    followupdate_end: Optional[str] = Query(None, description="Follow-up end date (YYYY-MM-DD)"),
    
    # Search
    search: Optional[str] = Query(None, description="Search term for name, phone, or email"),
    
    # Sorting
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    Get student leads with filtering, search, and sorting (no pagination)
    """
    try:
        # 1. Build base query - select only student profiles (is_active = 0)
        query = db.table('profiles').select('*').eq('is_active', 0)
        
        # 2. Apply filters one by one
        
        # Counsellor filter
        if counsellor:
            counsellor_list = [c.strip() for c in counsellor.split(',')]
            query = query.in_('counselled_by', counsellor_list)
        
        # Lead source filter
        if lead_source:
            source_list = [s.strip() for s in lead_source.split(',')]
            query = query.in_('lead_source', source_list)
        
        # Slot preference filter
        if slot_preference:
            slot_list = [s.strip() for s in slot_preference.split(',')]
            query = query.in_('slot_preference', slot_list)
        
        # Course filter (single course from dropdown)
        if course:
            query = query.ilike('interested_courses', f'%{course.strip()}%')
        
        # Created date range filter
        if start_date:
            query = query.gte('created_at', f'{start_date}T00:00:00')
        if end_date:
            query = query.lte('created_at', f'{end_date}T23:59:59')
        
        # Follow-up date range filter
        if followupdate_start:
            query = query.gte('next_follow_up', f'{followupdate_start}T00:00:00')
        if followupdate_end:
            query = query.lte('next_follow_up', f'{followupdate_end}T23:59:59')
        
        # Search filter
        if search:
            search_term = search.strip()
            query = query.or_(f'name.ilike.%{search_term}%,phone_number.ilike.%{search_term}%,email.ilike.%{search_term}%')
        
        # 3. Apply sorting (no pagination - get all records)
        query = query.order(sort_by, desc=(sort_order == "desc"))
        
        # 4. Execute the query (get all matching records)
        result = await query.execute()
        
        # 5. Format data for frontend
        formatted_data = []
        for lead in result.data:
            # Parse interested_courses JSON string to array
            interested_courses = []
            if lead.get('interested_courses'):
                try:
                    interested_courses = json.loads(lead['interested_courses'])
                except:
                    interested_courses = []
            
            formatted_lead = {
                "id": lead.get('id'),
                "user_id": lead.get('user_id'),
                "student_name": lead.get('name', ''),
                "phone_number": lead.get('phone_number', ''),
                "email": lead.get('email', ''),
                "place": lead.get('place', ''),
                "state": lead.get('state', ''),
                "country": lead.get('country', ''),
                "purpose": lead.get('purpose', ''),
                "college_name": lead.get('college_name', ''),
                "passout_year": lead.get('passout_year'),
                "degree": lead.get('degree', ''),
                "lead_source": lead.get('lead_source', ''),
                "mode": lead.get('mode', ''),
                "slot_preference": lead.get('slot_preference', ''),
                "counselled_by": lead.get('counselled_by', ''),
                "urgency": lead.get('urgency', ''),
                "interested_courses": interested_courses,
                "comments": lead.get('comments', ''),
                "send_brochure": lead.get('send_brochure', False),
                "fee_quoted": lead.get('fee_quoted'),
                "lead_quality": lead.get('lead_quality', ''),
                "is_verified": lead.get('is_verified', 0),
                "additional_people": lead.get('additional_people', 0),
                "next_follow_up": lead.get('next_follow_up'),
                "created_at": lead.get('created_at'),
                "updated_at": lead.get('updated_at')
            }
            formatted_data.append(formatted_lead)
        
        return JSONResponse(
            content={
                "success": True,
                "data": formatted_data,
                "total": len(formatted_data),
                "filters_applied": {
                    "counsellor": counsellor.split(',') if counsellor else [],
                    "lead_source": lead_source.split(',') if lead_source else [],
                    "slot_preference": slot_preference.split(',') if slot_preference else [],
                    "course": course or "",
                    "start_date": start_date or "",
                    "end_date": end_date or "",
                    "followupdate_start": followupdate_start or "",
                    "followupdate_end": followupdate_end or "",
                    "search": search or ""
                }
            }
        )
        
    except Exception as e:
        print(f"Error fetching leads: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to fetch student leads",
                "error": str(e)
            }
        )


@router.get("/leads/{lead_id}")
@auth_required(['counsellor', 'admin'])
async def get_student_lead_details(
    lead_id: int,
    request: Request,
    db: AsyncClient = Depends(get_db)
):
    """
    Get detailed information for a specific student lead using Supabase SDK methods
    """
    try:
        # Fetch lead details using .eq() method
        result = await db.table('profiles').select('*').eq('id', lead_id).eq('is_active', 0).single().execute()
        
        if not result.data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "Lead not found"
                }
            )
        
        lead = result.data
        
        # Map is_verified to status
        status_mapping = {
            0: 'new',
            1: 'contacted',
            2: 'qualified',
            3: 'converted',
            4: 'rejected'
        }
        
        # Parse interested courses if it's JSON string
        interested_courses = []
        if lead.get('interested_courses'):
            try:
                if isinstance(lead['interested_courses'], str):
                    import json
                    try:
                        interested_courses = json.loads(lead['interested_courses'])
                    except json.JSONDecodeError:
                        interested_courses = [course.strip() for course in lead['interested_courses'].split(',') if course.strip()]
                elif isinstance(lead['interested_courses'], list):
                    interested_courses = lead['interested_courses']
            except:
                interested_courses = []
        
        formatted_lead = {
            "id": lead.get('id'),
            "user_id": lead.get('user_id'),
            "student_name": lead.get('name', ''),
            "phone_number": lead.get('phone_number', ''),
            "email": lead.get('email', ''),
            "status": status_mapping.get(lead.get('is_verified', 0), 'new'),
            "location": lead.get('place', ''),
            "state": lead.get('state', ''),
            "country": lead.get('country', ''),
            "purpose": lead.get('purpose', ''),
            "college_name": lead.get('college_name', ''),
            "passout_year": lead.get('passout_year'),
            "degree": lead.get('degree', ''),
            "lead_source": lead.get('lead_source', ''),
            "mode": lead.get('mode', ''),
            "slot_preference": lead.get('slot_preference', ''),
            "counselled_by": lead.get('counselled_by', ''),
            "urgency": lead.get('urgency', ''),
            "interested_courses": interested_courses,
            "comments": lead.get('comments', ''),
            "send_brochure": lead.get('send_brochure', False),
            "fee_quoted": lead.get('fee_quoted'),
            "lead_quality": lead.get('lead_quality', ''),
            "additional_people": lead.get('additional_people', 0),
            "created_at": lead.get('created_at'),
            "updated_at": lead.get('updated_at')
        }
        
        return JSONResponse(
            content={
                "success": True,
                "data": formatted_lead
            }
        )
        
    except Exception as e:
        print(f"Error fetching lead details: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to fetch lead details",
                "error": str(e)
            }
        )


@router.post("/leads/{lead_id}/comment")
@auth_required(['counsellor', 'admin'])
async def update_lead_comment(
    lead_id: int,
    request: Request,
    db: AsyncClient = Depends(get_db)
):
    """
    Update comment for a specific lead using Supabase SDK methods
    """
    try:
        # Get comment from request body
        body = await request.json()
        comment = body.get('comment', '').strip()
        
        # Update the lead comment using .update() and .eq() methods
        result = await db.table('profiles').update({
            'comments': comment,
            'updated_at': 'now()'
        }).eq('id', lead_id).eq('is_active', 0).eq('role', 'student').execute()
        
        if not result.data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "Lead not found or update failed"
                }
            )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "Comment updated successfully",
                "data": {
                    "id": lead_id,
                    "comment": comment
                }
            }
        )
        
    except Exception as e:
        print(f"Error updating comment: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to update comment",
                "error": str(e)
            }
        )


# Additional useful endpoints you might want to add:

@router.patch("/leads/{lead_id}/status")
@auth_required(['counsellor', 'admin'])
async def update_lead_status(
    lead_id: int,
    request: Request,
    db: AsyncClient = Depends(get_db)
):
    """
    Update status for a specific lead using Supabase SDK methods
    """
    try:
        body = await request.json()
        new_status = body.get('status', '').strip().lower()
        
        # Validate status
        status_mapping = {
            'new': 0,
            'contacted': 1,
            'qualified': 2,
            'converted': 3,
            'rejected': 4
        }
        
        if new_status not in status_mapping:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Invalid status. Must be one of: {', '.join(status_mapping.keys())}"
                }
            )
        
        # Update the lead status using .update() and .eq() methods
        result = await db.table('profiles').update({
            'is_verified': status_mapping[new_status],
            'updated_at': 'now()'
        }).eq('id', lead_id).eq('is_active', 0).execute()
        
        if not result.data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "Lead not found or update failed"
                }
            )
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Lead status updated to {new_status}",
                "data": {
                    "id": lead_id,
                    "status": new_status
                }
            }
        )
        
    except Exception as e:
        print(f"Error updating lead status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to update lead status",
                "error": str(e)
            }
        )


@router.get("/leads/stats/summary")
@auth_required(['counsellor', 'admin'])
async def get_leads_summary_stats(
    request: Request,
    db: AsyncClient = Depends(get_db)
):
    """
    Get summary statistics for leads using Supabase SDK methods
    """
    try:
        # Get total leads count
        total_result = await db.table('profiles').select('id', count='exact').eq('is_active', 0).execute()
        total_leads = total_result.count
        
        # Get status distribution
        status_stats = {}
        status_mapping = {
            0: 'new',
            1: 'contacted', 
            2: 'qualified',
            3: 'converted',
            4: 'rejected'
        }
        
        for status_value, status_name in status_mapping.items():
            result = await db.table('profiles').select('id', count='exact').eq('is_active', 0).eq('is_verified', status_value).execute()
            status_stats[status_name] = result.count
        
        # Get recent leads (last 7 days)
        from datetime import datetime, timedelta
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        recent_result = await db.table('profiles').select('id', count='exact').eq('is_active', 0).gte('created_at', seven_days_ago).execute()
        recent_leads = recent_result.count
        
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "total_leads": total_leads,
                    "recent_leads": recent_leads,
                    "status_distribution": status_stats,
                    "conversion_rate": round((status_stats.get('converted', 0) / total_leads * 100), 2) if total_leads > 0 else 0
                }
            }
        )
        
    except Exception as e:
        print(f"Error fetching leads summary: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to fetch leads summary",
                "error": str(e)
            }
        )
        
    except Exception as e:
        print(f"Error updating comment: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Failed to update comment",
                "error": str(e)
            }
        )