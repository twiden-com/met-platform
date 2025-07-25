from typing import Optional, List, Callable, Any
from pydantic import BaseModel
from functools import wraps
from fastapi import APIRouter, Depends, status, HTTPException,Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from src.config.database import get_admin_db, get_db
from inspect import iscoroutinefunction
# =====================================================
# GET LOGGEDIN USER
# =====================================================
class UserData(BaseModel):
    user: Any
    profile: Any

def auth_required(roles: List[str] = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            # Read session cookie
            session_token = request.cookies.get('user_session')
            
            if not session_token:
                return _redirect_to_login()
            
            try:
                # Get database connection (you'll need to adjust this)
                db = await get_db() # Get DB instance
                
                # Validate session and get user
                result = await db.auth.get_user(session_token)
                if not result:
                    return _redirect_to_login()
                
                # Fetch user profile
                user_profile = await db.table('profiles').select('*').eq('user_id', result.user.id).single().execute()
                if not user_profile:
                    return _redirect_to_login()
                
                role = user_profile.data.get('role')

                # Check role permissions
                if roles and role not in roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required roles: {roles}"
                    )
                
                # Set all data in request state
                request.state.user_data = UserData(
                    user=result.user,
                    profile=user_profile.data
                )
                
                # Call the original function
                if iscoroutinefunction(func):
                    return await func(request, *args, **kwargs)
                else:
                    return func(request, *args, **kwargs)
                
            except Exception as e:
                # Log error and redirect on any other failure
                print(f"Auth error: {e}")  # Replace with proper logging
                return _redirect_to_login()
        
        return wrapper
    return decorator

def _redirect_to_login():
    """Helper to create login redirect response"""
    response = RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie("user_session")
    return response