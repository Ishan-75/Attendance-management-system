from datetime import datetime, date, time
import zoneinfo
from app.core.config import settings


def get_timezone() -> zoneinfo.ZoneInfo:
    try:
        return zoneinfo.ZoneInfo(settings.APP_TIMEZONE)
    except Exception:
        return zoneinfo.ZoneInfo("UTC")


def get_current_datetime() -> datetime:
    return datetime.now(get_timezone())


def get_current_date() -> date:
    return get_current_datetime().date()


def get_current_time() -> time:
    return get_current_datetime().time()


def to_app_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        # If naive, assume UTC or app timezone
        return dt.replace(tzinfo=get_timezone())
    return dt.astimezone(get_timezone())
