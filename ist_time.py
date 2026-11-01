"""IST time helpers for TryIT scripts"""
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    """Current time in IST"""
    return datetime.now(IST)

def to_ist(utc_str):
    """Convert Supabase UTC timestamp string to IST"""
    if not utc_str:
        return ""
    try:
        # Handle both with and without timezone suffix
        dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST)
    except Exception:
        return utc_str[:19] if len(utc_str) > 19 else utc_str

def to_ist_str(utc_str, fmt='%Y-%m-%d %H:%M:%S IST'):
    """Convert to formatted IST string"""
    dt = to_ist(utc_str)
    if isinstance(dt, datetime):
        return dt.strftime(fmt)
    return str(dt)

def ist_day_utc_range(ist_date):
    """Given an IST date (YYYY-MM-DD), return (start_utc, end_utc) for that IST day."""
    from datetime import date
    if isinstance(ist_date, str):
        ist_date = date.fromisoformat(ist_date)
    ist_start = datetime.combine(ist_date, datetime.min.time()).replace(tzinfo=IST)
    ist_end = ist_start + timedelta(days=1)
    return ist_start.astimezone(timezone.utc).isoformat(), ist_end.astimezone(timezone.utc).isoformat()

if __name__ == "__main__":
    print(f"🕐 Now in IST: {now_ist().strftime('%Y-%m-%d %H:%M:%S')}")
