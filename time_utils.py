from datetime import date, datetime

FIXED_DATE = None
#Usage example: FIXED_DATE = date(2026, 2, 25)


def get_now():
    real_now = datetime.now()
    if FIXED_DATE is None:
        return real_now
    return datetime.combine(FIXED_DATE, real_now.time())


def get_today():
    return FIXED_DATE or date.today()
