from supabase import AsyncClient, acreate_client
from functools import lru_cache
from src.config.settings import settings
from typing import Optional
# # @lru_cache()
# async def get_db() -> AsyncClient:
#     return await acreate_client(settings.supabase_url, settings.supabase_key)

# # @lru_cache()
# async def get_admin_db() -> AsyncClient:
#     return await acreate_client(settings.supabase_url, settings.supabase_service_key)


_db_client: Optional[AsyncClient] = None
_admin_client: Optional[AsyncClient] = None

async def get_db() -> AsyncClient:
    """Get or create database client"""
    global _db_client
    if _db_client is None:
        _db_client = await acreate_client(
            settings.supabase_url, 
            settings.supabase_key
        )
    return _db_client

async def get_admin_db() -> AsyncClient:
    """Get or create admin client"""
    global _admin_client
    if _admin_client is None:
        _admin_client = await acreate_client(
            settings.supabase_url, 
            settings.supabase_service_key
        )
    return _admin_client