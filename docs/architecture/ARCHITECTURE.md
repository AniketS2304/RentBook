# Architecture — RentBook

## Overview

RentBook is a mobile-first digital rent register with a unified FastAPI + PostgreSQL backend serving two client applications:
1. **Android Native App (`apps/mobile`)**: React Native + Expo (TypeScript, Expo Router, NativeWind), distributed directly via standalone APK.
2. **Mobile Web App (`apps/web`)**: React + Vite (TypeScript, Tailwind CSS), optimized for iPhone Safari and mobile browsers.

```text
                    ┌───────────────────┐
                    │   PostgreSQL      │
                    └─────────▲─────────┘
                              │
                    ┌─────────┴─────────┐
                    │     FastAPI       │
                    │                   │
                    │ Auth              │
                    │ Business Logic    │
                    │ Rent Calculation  │
                    │ Payments          │
                    │ Dashboard         │
                    │ Reminders         │
                    └─────────▲─────────┘
                              │ HTTPS REST API
                 ┌────────────┴────────────┐
                 │                         │
        ┌────────┴────────┐       ┌────────┴────────┐
        │ React Native    │       │ React + Vite    │
        │ Expo            │       │ Mobile Web      │
        │ Android (APK)   │       │ iPhone Safari   │
        └─────────────────┘       └─────────────────┘
```

---

## Monorepo Directory Structure

```text
RentBook/
├── apps/
│   ├── mobile/          # Android native app (Expo managed workflow, React Native, TypeScript)
│   │   ├── app/         # Expo Router file-based screens
│   │   ├── components/  # Native UI components (NativeWind styled)
│   │   ├── hooks/       # API and query hooks
│   │   ├── services/    # Client API service calling FastAPI
│   │   └── package.json
│   │
│   ├── web/             # Mobile web app (React, Vite, TypeScript, Tailwind CSS)
│   │   ├── src/
│   │   │   ├── components/ # Web UI components (Tailwind CSS)
│   │   │   ├── pages/      # Route pages
│   │   │   ├── services/   # Client API service calling FastAPI
│   │   │   └── App.tsx
│   │   └── package.json
│   │
│   └── api/             # Backend API (FastAPI, SQLAlchemy, Alembic, PostgreSQL)
│       ├── app/
│       │   ├── api/          # Route controllers (thin HTTP layer)
│       │   ├── core/         # Config, security, dependencies
│       │   ├── models/       # SQLAlchemy ORM models
│       │   ├── repositories/ # Data access layer (mandatory owner_id filtering)
│       │   ├── schemas/      # Pydantic v2 schemas
│       │   └── services/     # Business logic & status computation (Single Source of Truth)
│       ├── alembic/          # Database migrations
│       └── requirements.txt
├── docs/                # Comprehensive product & architecture specifications
├── AGENTS.md            # Agent rules and domain guidelines
└── README.md
```

---

## Backend Architecture (`apps/api`)

### Layer Responsibilities

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Routes** | `app/api/` | HTTP endpoints. Request parsing, response formatting, auth enforcement. |
| **Services** | `app/services/` | Business logic. Rent calculation, status computation, validation rules. (Single Source of Truth) |
| **Repositories** | `app/repositories/` | Database queries. CRUD operations, filtered by `owner_id`. |
| **Models** | `app/models/` | SQLAlchemy ORM models. |
| **Schemas** | `app/schemas/` | Pydantic models for request/response validation. |
| **Core** | `app/core/` | Configuration, security utilities, dependencies. |

### Key Principles

1. **Routes are thin** — They call services, they don't contain business logic.
2. **Services contain all business logic** — Status calculation, validation, on-demand rent generation.
3. **Repositories handle data access** — All database queries go through repositories.
4. **`owner_id` filtering happens in repositories** — Every query accessing user-owned data filters by `owner_id`. This is the primary security boundary.
5. **No direct ORM usage in routes** — Routes use services, services use repositories.
6. **Client-Agnostic API** — The backend serves identical JSON responses to both Android and Web clients.

### Authentication Flow

```text
Client (Android APK or Mobile Web) sends request with Authorization: Bearer <JWT>
→ Auth middleware extracts and validates JWT
→ Extracts owner_id from token claims
→ owner_id is injected into route handler as dependency
→ All downstream queries filter by owner_id
```

### Error Handling

- Validation errors → `422 Unprocessable Entity` with field-level details
- Resource not found or not owned by user → `404 Not Found` (prevents leaking existence)
- Authentication failures / Missing token → `401 Unauthorized`
- Forbidden action (e.g. account inactive) → `403 Forbidden`
- Sanity check warnings (e.g. 2x rent payment) → `422` with machine-readable code `EXCESSIVE_AMOUNT_WARNING`
- Server errors → `500 Internal Server Error` (logged, not exposed to client)

---

## Client Applications Architecture

### Common Principles Across Both Clients

1. **Zero Business Logic on Clients**: Rent status, collection sums, and eligibility boundaries are computed by the backend. Clients render received states and capture input.
2. **Mobile-First UX**: Navigation, touch targets, and typography are optimized for single-hand smartphone use (360px–414px width).
3. **State Management**: Server state managed via React Query (or similar cache). Minimal client-side state.
4. **All States Handled**: Loading, error, empty, and success states are explicitly handled for every data-fetching view.

### 1. Android Native App (`apps/mobile`)

- **Primary technology**: React Native with Expo (Managed Workflow), TypeScript.
- **Routing**: Expo Router using bottom tabs (`Home`, `Properties`, `Rent`, `Settings`) and native modal/push stacks.
- **Styling**: NativeWind for Tailwind utility parity.
- **Platform Features**:
  - Android hardware/gesture back button handling.
  - Native `KeyboardAvoidingView` to prevent inputs from being obscured.
  - Native WhatsApp launching via `Linking.openURL('whatsapp://send?...')` or `https://wa.me/...`.
  - Secure credential storage using `expo-secure-store`.

### 2. Mobile Web App (`apps/web`)

- **Primary technology**: React + Vite, TypeScript, Tailwind CSS.
- **Target environment**: Mobile browsers, primarily iPhone Safari.
- **Platform Features**:
  - Safe area handling (`env(safe-area-inset-top)`, `env(safe-area-inset-bottom)`).
  - Dynamic viewport height support (`100dvh`) to avoid Safari mobile toolbar resizing issues.
  - WhatsApp launching via `window.open('https://wa.me/...', '_blank')`.
  - Touch-optimized tap targets (minimum 44x44px) without hover state artifacts.

---

## Data Flow Example: Record Payment

```text
1. Landlord taps "Pay" on overdue tenant in Android app or iPhone Safari
2. Client shows payment form (amount pre-filled, method selector, date picker)
3. Landlord selects "Cash", confirms
4. Client POSTs to /api/v1/rent/{rent_id}/payments
   Body: { amount_paise: 800000, payment_method: "CASH", paid_date: "2026-10-05", notes: "", confirm_excess: false }
   Header: Authorization: Bearer <jwt>

5. Backend route:
   → Validates JWT → extracts owner_id
   → Calls PaymentService.record_payment(owner_id, rent_id, payment_data)

6. PaymentService:
   → Calls RentRepository.get_by_id(rent_id, owner_id)  # ownership check (returns 404 if not owned)
   → Validates amount (> 0, sanity check against 2x expected)
   → Calls PaymentRepository.create(payment_data)
   → Computes updated rent status dynamically

7. Client receives 201 Created
   → Invalidates dashboard cache
   → Shows success feedback
   → Navigates back to previous screen
```

---

## Deployment Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                      Server / VPS                       │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │                     Nginx                         │  │
│  │  - SSL / HTTPS Termination                        │  │
│  │  - Reverse proxy /api/* → FastAPI                 │  │
│  │  - Static file hosting / → React Mobile Web dist  │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │ HTTP                          │
│                         ▼                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │             FastAPI Backend (Docker)              │  │
│  │                  Port 8000                        │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │ SQL                           │
│                         ▼                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │             PostgreSQL 16 (Docker)                │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Android Distribution (Client)              │
│                                                         │
│  React Native Expo (apps/mobile)                        │
│          ↓                                              │
│  EAS Build (Expo Application Services)                  │
│          ↓                                              │
│  RentBook.apk (Standalone Android APK)                  │
│          ↓                                              │
│  Direct distribution via WhatsApp / Direct Download     │
│  Installed directly on landlord's Android phone         │
└─────────────────────────────────────────────────────────┘
```

### Environment Configuration

All configuration via environment variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry |
| `CORS_ORIGINS` | Allowed frontend web origins |
| `ENVIRONMENT` | `dev` / `staging` / `production` |

**No credentials in source code or client bundles. Ever.**
