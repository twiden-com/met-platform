from functools import wraps
from inspect import iscoroutinefunction
from fastapi import APIRouter, Depends, status, HTTPException,Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from src.config.database import get_admin_db, get_db
from supabase import Client, AsyncClient    
from src.external.messagecentral import send_otp, verify_otp
import json
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/auth", tags=["Authentication"])

templates = Jinja2Templates(directory="templates", auto_reload=True)


# =====================================================
# SIGNUP USER
# =====================================================
@router.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
     return await templates.TemplateResponse("medha/login.html", {"request": request})

@router.post("/signup")
async def signup_submit(
        request  : Request, 
        db       : AsyncClient = Depends(get_db), 
        admin_db : AsyncClient = Depends(get_admin_db)
    ):
    try:
        auth_result = await admin_db.auth.sign_up({
            "email"   : request.email,
            "password": request.password,
        })
        
        profile = await db.table("profiles").insert({
            "id"       : auth_result.user.id,
            "email"    : request.email,
            "full_name": request.full_name,
        }).execute()
        
        return {
            "user"    : auth_result.user,
            "profile" : profile.data[0],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# LOGIN USER WITH EMAIL & PASSWORD
# =====================================================
@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
     return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_submit(request: Request, db = Depends(get_db)):
    try:
        result = await db.auth.sign_in_with_password({
            "email"   : request.email,
            "password": request.password
        })
        
        return {"user": result.user, "session": result.session}

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# =====================================================
# LOGIN USER WITH PHONE & OTP
# =====================================================
@router.post("/send/phone_otp")
def login_send_otp(country_code:str, phone: str): #Eg. country_code - 91, phone - 7013908751 
    try:
        res = send_otp(country_code=country_code, phone=phone)
        return json.loads(res.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@router.post("/verify/phone_otp")
async def validate_otp(phone:str, country_code:str, otp: str, verification_id: str, db:AsyncClient = Depends(get_db)): #Eg. otp - 287976 
    try:
        res = verify_otp(code=otp, verification_id=verification_id, country_code=country_code, phone=phone)
        
        if res.status_code == 200:
            data = json.loads(res.text)
            if data.get("message") == 'VERIFICATION_EXPIRED':
                
                return data
            
            elif data.get("message") == 'SUCCESS':
                
                email = password = country_code + '-' + phone + "@met.com"
                
                result = await db.auth.sign_in_with_password(
                    {
                        "email"   : email,
                        "password": password,
                    }
                )

                profile = await db.table("profiles").select("id", "phone_number", "role").eq("user_id", result.user.id).execute()

                profile = profile.data[0]

                # Create JSONResponse
                response = JSONResponse(
                    content={
                        "success": True,
                        "redirect": True,
                        "redirectUrl": f"/{profile.get('role')}/dashboard"
                    }
                )

                response.set_cookie(
                    key="user_session",
                    value=result.session.access_token,
                    httponly=True,
                    secure=True,
                    samesite='lax',
                    max_age=3600
                )

                return response

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


    

    