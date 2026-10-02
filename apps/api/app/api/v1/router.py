from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, properties, rent, tenants, units

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
