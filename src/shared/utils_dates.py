import datetime
from pytz import timezone
from core.settings import settings



def get_app_current_time(tz: str = settings.TIME_ZONE) -> datetime.datetime:
    return datetime.datetime.now(timezone(tz))

