# Architecture — RentBook

## Overview

RentBook is a monolithic web application with a React frontend and FastAPI backend, backed by PostgreSQL. It is deployed as Docker containers behind Nginx.

```
┌─────────────────────────────────────────────────────┐
│                    Client (Browser)                  │
│               React + Tailwind CSS                   │
│              Mobile-responsive SPA                   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────┐
│                      Nginx                           │
│          Reverse proxy + static files                │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (internal)
                       ▼
┌─────────────────────────────────────────────────────┐
│                    FastAPI                            │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Routes   │→│ Services  │→│  Repositories     │  │
│  │  (API)    │  │ (Logic)  │  │  (Data Access)   │  │
│  └──────────┘  └──────────┘  └────────┬─────────┘  │
│                                        │             │
│  ┌──────────────────────────────────┐  │             │
│  │  Auth Middleware (JWT + owner_id) │  │             │
│  └──────────────────────────────────┘  │             │
└────────────────────────────────────────┼─────────────┘
                                         │ SQL
                                         ▼
┌─────────────────────────────────────────────────────┐
│                   PostgreSQL                         │
│              All application data                    │
└─────────────────────────────────────────────────────┘
```

## Backend Architecture

### Layer Responsibilities

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Routes** | `app/api/` | HTTP endpoints. Request parsing, response formatting, auth enforcement. |
| **Services** | `app/services/` | Business logic. Rent calculation, status computation, validation rules. |
| **Repositories** | `app/repositories/` | Database queries. CRUD operations, filtered by owner_id. |
| **Models** | `app/models/` | SQLAlchemy ORM models. |
| **Schemas** | `app/schemas/` | Pydantic models for request/response validation. |
| **Core** | `app/core/` | Configuration, security utilities, dependencies. |

### Key Principles

1. **Routes are thin** — They call services, they don't contain business logic.
2. **Services contain all business logic** — Status calculation, validation, rent generation.
3. **Repositories handle data access** — All database queries go through repositories.
4. **owner_id filtering happens in repositories** — Every query that accesses tenant-owned data filters by owner_id. This is the primary security boundary.
5. **No direct ORM usage in routes** — Routes use services, services use repositories.

### Authentication Flow

```
Client sends request with Authorization: Bearer <JWT>
→ Auth middleware extracts and validates JWT
→ Extracts owner_id from token claims
→ owner_id is injected into route handler as dependency
→ All downstream queries filter by owner_id
```

### Error Handling

- Validation errors → 422 with field-level details
- Not found → 404
- Authorization failures → 403
- Authentication failures → 401
- Server errors → 500 (logged, not exposed to client)

## Frontend Architecture

### Structure

```
src/
├── components/          # Reusable UI components
│   ├── common/          # Buttons, inputs, cards, modals
│   ├── dashboard/       # Dashboard-specific components
│   ├── property/        # Property-related components
│   ├── tenant/          # Tenant-related components
│   └── rent/            # Rent/payment components
├── pages/               # Page-level components (one per route)
├── hooks/               # Custom React hooks
├── services/            # API client functions
├── context/             # React context (auth, etc.)
├── utils/               # Formatters, helpers
└── types/               # TypeScript type definitions
```

### Key Principles

1. **Mobile-first** — All layouts designed for mobile screens first, then adapted for desktop.
2. **Minimal state** — Server state managed via React Query (or similar). Minimal client-side state.
3. **Loading/error/empty states** — Every data-fetching component handles all three states.
4. **No business logic in frontend** — The frontend displays data and captures input. Business rules live in the backend.

### Routing

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Dashboard | Monthly summary, overdue list, recent payments |
| `/properties` | Properties List | All owner's properties |
| `/properties/:id` | Property Detail | Units within property, vacancy view |
| `/properties/:id/units/new` | Add Unit | Create unit form |
| `/units/:id` | Unit Detail | Unit info, current tenant |
| `/tenants` | Tenants List | All tenants across properties |
| `/tenants/:id` | Tenant Detail | Tenant info, rent history |
| `/rent` | Rent Overview | Current month's rent status across all properties |
| `/rent/:id/pay` | Record Payment | Payment recording form |
| `/login` | Login | Authentication |
| `/register` | Register | Registration |
| `/settings` | Settings | Owner profile, preferences |

## Deployment Architecture

### Docker Compose (Development & Production)

```yaml
services:
  frontend:     # Node dev server (dev) or built static files (prod)
  backend:      # FastAPI with uvicorn
  db:           # PostgreSQL 16
  nginx:        # Reverse proxy (production only)
```

### Environment Configuration

All configuration via environment variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry |
| `CORS_ORIGINS` | Allowed frontend origins |
| `ENVIRONMENT` | dev / staging / production |

**No credentials in source code. Ever.**

## Data Flow Example: Record Payment

```
1. Owner taps "Record Payment" on tenant's overdue rent
2. Frontend shows payment form (amount pre-filled, method selector, date picker)
3. Owner selects "Cash", confirms
4. Frontend POSTs to /api/rent/{rent_id}/payments
   Body: { amount: 800000, method: "CASH", paid_date: "2026-10-05", notes: "" }
   Header: Authorization: Bearer <jwt>

5. Backend route:
   → Validates JWT → extracts owner_id
   → Calls PaymentService.record_payment(owner_id, rent_id, payment_data)

6. PaymentService:
   → Calls RentRepository.get_by_id(rent_id, owner_id)  # ownership check
   → Validates amount (> 0, sanity check against expected)
   → Calls PaymentRepository.create(payment_data)
   → Returns updated rent record with new status

7. Frontend receives 201 Created
   → Invalidates dashboard cache
   → Shows success toast
   → Navigates back to previous screen
```

## Performance Considerations

For MVP scale (< 1000 users, < 10,000 rent records per owner):

- No caching layer needed
- No background job queue needed
- No search engine needed
- PostgreSQL indexes on foreign keys and common query patterns are sufficient
- Single server deployment is adequate

**Do not add infrastructure complexity prematurely.**
