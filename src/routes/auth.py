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

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
     return templates.TemplateResponse("login.html", {"request": request})

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
async def login_validate_otp(phone:str, country_code:str, otp: str, verification_id: str, db:AsyncClient = Depends(get_db)): #Eg. otp - 287976 
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
                        "redirectUrl": "/dashboard"
                    }
                )

                # Set access token cookie
                response.set_cookie(
                    key="user_session",
                    value=result.session.access_token,
                    httponly=True,
                    secure=True,
                    samesite='lax',
                    max_age=86400  # 24 hours
                )

                # Set refresh token cookie (this is the key!)
                response.set_cookie(
                    key="refresh_token",
                    value=result.session.refresh_token,
                    httponly=True,
                    secure=True,
                    samesite='lax',
                    max_age=604800  # 7 days
                )

                return response

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


    

@router.get("/logout")
async def logout_user(request: Request):
    # Get tokens from cookies
    session_token = request.cookies.get('user_session')
    refresh_token = request.cookies.get('refresh_token')
    
    # Invalidate Supabase session if tokens exist
    if session_token or refresh_token:
        try:
            db = await get_db()
            if session_token and refresh_token:
                await db.auth.set_session(
                    access_token=session_token,
                    refresh_token=refresh_token
                )
            await db.auth.sign_out()
        except:
            pass  # Continue even if Supabase logout fails
    
    # Clear cookies and redirect
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("user_session")
    response.delete_cookie("refresh_token")
    return response