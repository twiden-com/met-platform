from supabase import AsyncClient, acreate_client
from functools import lru_cache
from src.config.settings import settings

@lru_cache()
async def get_db() -> AsyncClient:
    return await acreate_client(settings.supabase_url, settings.supabase_key)

@lru_cache()
async def get_admin_db() -> AsyncClient:
    return await acreate_client(settings.supabase_url, settings.supabase_service_key)