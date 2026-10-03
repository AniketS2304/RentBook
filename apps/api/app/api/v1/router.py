from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    dashboard,
    health,
    payments,
    properties,
    reminders,
    rent,
    reports,
    tenants,
    units,
)

api_v1_router = APIRouter()

# Health endpoints
api_v1_router.include_router(health.router)

# Auth endpoints
api_v1_router.include_router(auth.router)

# Property endpoints
api_v1_router.include_router(properties.router)

# Unit endpoints
api_v1_router.include_router(units.router)

# Tenant endpoints
api_v1_router.include_router(tenants.router)

# Rent endpoints
api_v1_router.include_router(rent.router)

# Payment endpoints
api_v1_router.include_router(payments.router)

# Dashboard endpoints
api_v1_router.include_router(dashboard.router)

# Reminders endpoints
api_v1_router.include_router(reminders.router)

# Reports endpoints
api_v1_router.include_router(reports.router)



