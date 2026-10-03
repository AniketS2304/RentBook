from app.repositories.base import BaseOwnerScopedRepository
from app.repositories.dashboard import DashboardRepository, dashboard_repo
from app.repositories.owner import OwnerRepository, owner_repo
from app.repositories.payment import PaymentRepository, payment_repo
from app.repositories.property import PropertyRepository, property_repo
from app.repositories.reminder import ReminderRepository, reminder_repo
from app.repositories.rent_record import RentRecordRepository, rent_repo
from app.repositories.tenant import TenantRepository, tenant_repo
from app.repositories.unit import UnitRepository, unit_repo

__all__ = [
    "BaseOwnerScopedRepository",
    "DashboardRepository",
    "dashboard_repo",
    "OwnerRepository",
    "owner_repo",
    "PaymentRepository",
    "payment_repo",
    "PropertyRepository",
    "property_repo",
    "ReminderRepository",
    "reminder_repo",
    "RentRecordRepository",
    "rent_repo",
    "TenantRepository",
    "tenant_repo",
    "UnitRepository",
    "unit_repo",
]
