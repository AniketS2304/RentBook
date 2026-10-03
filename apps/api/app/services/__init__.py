from app.services.auth import AuthService, auth_service
from app.services.dashboard import DashboardService, dashboard_service
from app.services.payment import PaymentService, payment_service
from app.services.property import PropertyService, property_service
from app.services.reminder import ReminderService, reminder_service
from app.services.rent import RentService, rent_service
from app.services.rent_status import calculate_rent_status, get_today_ist
from app.services.tenant import TenantService, tenant_service
from app.services.unit import UnitService, unit_service

__all__ = [
    "AuthService",
    "auth_service",
    "DashboardService",
    "dashboard_service",
    "PaymentService",
    "payment_service",
    "PropertyService",
    "property_service",
    "ReminderService",
    "reminder_service",
    "RentService",
    "rent_service",
    "calculate_rent_status",
    "get_today_ist",
    "TenantService",
    "tenant_service",
    "UnitService",
    "unit_service",
]
