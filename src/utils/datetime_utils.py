from datetime import datetime, timezone

def utc_now() -> datetime:
    """Get current UTC time with timezone awareness"""
    return datetime.now(timezone.utc)

def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC if it has timezone info"""
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)