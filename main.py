from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.routes.auth import router as auth_router
from src.routes.dashboard import router as dashboard_router
from src.routes.leads import router as lead_router
from src.routes.student import router as student_router
from src.routes.batch import router as batch_router
from src.routes.medha_code import router as medha_code_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from src.config.settings import settings
from fastapi.responses import RedirectResponse
import uvicorn 
import time

app = FastAPI(
    title    ="Medha Platform",
    version  ="1.0.0",
    docs_url ="/docs",
    redoc_url="/redoc",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/health")
def health_check():
    return {
        "status"      : "healthy",
        "environment" : settings.environment,
        "timestamp"   : time.time()
    }

@app.get("/")
def root(request: Request):
    return RedirectResponse('/auth/login')

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(student_router)
app.include_router(batch_router)
app.include_router(lead_router)
app.include_router(medha_code_router)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "dev",
        workers=1 if settings.environment == "dev" else 4,
        log_level=settings.log_level.lower()
    )