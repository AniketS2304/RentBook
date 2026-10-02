from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

try:
    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = None


def get_today_ist() -> date:
    """Get current calendar date in Indian Standard Time (IST)."""
    if IST:
        return datetime.now(IST).date()
    return datetime.utcnow().date()


def calculate_rent_status(
    due_date: date,
    expected_amount_paise: int,
    total_paid_paise: int = 0,
    today: Optional[date] = None,
) -> str:
    """Centralized rent status computation function.

    Computes rent status dynamically according to BUSINESS_RULES.md (BR-RENT-08 to BR-RENT-11):
    - PAID: total_paid >= expected_amount
    - PARTIALLY_PAID: 0 < total_paid < expected_amount and today <= due_date
    - OVERDUE: total_paid < expected_amount and today > due_date
    - DUE: total_paid == 0 and today == due_date
    - PENDING: total_paid == 0 and today < due_date
    """
    if today is None:
        today = get_today_ist()

    if total_paid_paise >= expected_amount_paise:
        return "PAID"
    if total_paid_paise > 0:
        if today <= due_date:
            return "PARTIALLY_PAID"
        return "OVERDUE"
    # total_paid_paise == 0
    if today > due_date:
        return "OVERDUE"
    if today == due_date:
        return "DUE"
    return "PENDING"
