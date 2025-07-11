from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    supabase_url: str          = Field(..., min_length=1) 
    supabase_key: str          = Field(..., min_length=1) 
    supabase_service_key: str  = Field(..., min_length=1) 
    environment: str = "dev"
    port: int = 8000
    log_level: str = 'info'
    model_config = {"env_file": ".env"}

settings = Settings()
