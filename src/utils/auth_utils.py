from inspect import iscoroutinefunction
from typing import Optional, List, Callable, Any
from pydantic import BaseModel
from functools import wraps
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from src.config.database import get_admin_db, get_db

class UserData(BaseModel):
    user: Any
    profile: Any

def auth_required(roles: List[str] = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            # Read session cookie
            session_token = request.cookies.get('user_session')
            refresh_token = request.cookies.get('refresh_token')
            
            if not session_token:
                return _redirect_to_logout()
            
            try:
                # Get database connection
                db = await get_db()
                
                # Set session first if we have both tokens
                if session_token and refresh_token:
                    try:
                        await db.auth.set_session(
                            access_token=session_token,
                            refresh_token=refresh_token
                        )
                    except Exception as e:
                        print(f"Set session error: {e}")
                        return _redirect_to_logout()
                
                # Get current user
                user_result = await db.auth.get_user()
                if not user_result or not user_result.user:
                    return _redirect_to_logout()
                
                # Fetch user profile
                user_profile = await db.table('profiles').select('*').eq('user_id', user_result.user.id).single().execute()
                if not user_profile or not user_profile.data:
                    return _redirect_to_logout()
                
                role = user_profile.data.get('role')

                # Check role permissions
                if roles and role not in roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required roles: {roles}"
                    )
                
                # Set all data in request state
                request.state.user_data = UserData(
                    user=user_result.user,
                    profile=user_profile.data
                )
                
                # Call the original function
                response = None
                if iscoroutinefunction(func):
                    response = await func(request, *args, **kwargs)
                else:
                    response = func(request, *args, **kwargs)
                
                # Check if session was refreshed and update cookies
                current_session = await db.auth.get_session()
                if (current_session and 
                    hasattr(current_session, 'access_token') and 
                    current_session.access_token != session_token):
                    
                    if hasattr(response, 'set_cookie'):
                        response.set_cookie(
                            key="user_session",
                            value=current_session.access_token,
                            httponly=True,
                            secure=True,
                            samesite='lax',
                            max_age=86400
                        )
                        
                        if hasattr(current_session, 'refresh_token'):
                            response.set_cookie(
                                key="refresh_token",
                                value=current_session.refresh_token,
                                httponly=True,
                                secure=True,
                                samesite='lax',
                                max_age=604800
                            )
                
                return response
                
            except Exception as e:
                # Log error and redirect on any other failure
                print(f"Auth error: {e}")
                return _redirect_to_logout()
        
        return wrapper
    return decorator

def _redirect_to_logout():
    """Helper to create login redirect response"""
    response = RedirectResponse(
        url="/auth/logout",
        status_code=status.HTTP_303_SEE_OTHER
    )
    return response