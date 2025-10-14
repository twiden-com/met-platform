from fastapi import APIRouter, Depends, status, HTTPException,Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import json
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Marketing"])

templates = Jinja2Templates(directory="templates", auto_reload=True)

@router.get("/brochures", response_class=HTMLResponse)
async def show_brochures(request: Request):
     return templates.TemplateResponse("brochures.html", {"request": request})