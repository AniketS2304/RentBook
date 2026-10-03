# API Design — RentBook

## Conventions

- **Base URL**: `/api/v1`
- **Client Consumers**: Consumed identically by both the **Android Native App** (`apps/mobile`) and the **Mobile Web App** (`apps/web`). The API is completely client-agnostic with zero platform-specific routes.
- **Authentication**: Bearer JWT token in `Authorization` header (`Authorization: Bearer <token>`) on all endpoints except `/auth/*`.
- **Content-Type**: `application/json`
- **Monetary values**: Integers in paise (₹8,000 = 800000). The API accepts and returns paise. Client apps handle rupee formatting (`₹8,000`) for display.
- **Dates**: ISO 8601 format `YYYY-MM-DD` for dates, `YYYY-MM-DDTHH:MM:SSZ` for timestamps
- **IDs**: UUIDs
- **Pagination**: `?page=1&per_page=20` (default 20, max 100)
- **Errors**: Consistent error response format across all endpoints

### Error Response Format

```json
{
  "detail": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "errors": [
    {
      "field": "email",
      "message": "Email already registered"
    }
  ]
}
```

---

## Authentication

### POST /api/v1/auth/register

Register a new owner account.

**Request**:
```json
{
  "email": "landlord@example.com",
  "password": "securePassword123",
  "full_name": "Rajesh Kumar",
  "phone": "9876543210"
}
```

**Validation**:
- `email`: Required, valid email format, unique
- `password`: Required, minimum 8 characters
- `full_name`: Required, 2–100 characters
- `phone`: Optional, valid Indian phone format

**Response** (201 Created):
```json
{
  "id": "uuid",
  "email": "landlord@example.com",
  "full_name": "Rajesh Kumar",
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/login

**Request**:
```json
{
  "email": "landlord@example.com",
  "password": "securePassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "landlord@example.com",
    "full_name": "Rajesh Kumar"
  }
}
```

**Error** (401 Unauthorized):
```json
{
  "detail": "Invalid email or password",
  "code": "INVALID_CREDENTIALS"
}
```

### POST /api/v1/auth/refresh

Issue a new access token using a valid refresh token. On every refresh, **refresh-token rotation** occurs: the server issues a new short-lived access token (30 minutes) and rotates the refresh token (7 days). The client must replace the previous refresh token with the newly issued one.

**Request**:
```json
{
  "refresh_token": "refresh_token"
}
```

**Response** (200 OK):
```json
{
  "access_token": "new_jwt_token",
  "refresh_token": "new_rotated_refresh_token",
  "token_type": "bearer"
}
```

**Error** (401 Unauthorized):
```json
{
  "detail": "Invalid or expired refresh token",
  "code": "INVALID_REFRESH_TOKEN"
}
```

---

## Properties

### GET /api/v1/properties

List all properties for the authenticated owner.

**Query params**:
- `include_archived`: boolean (default: false)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Shree Residency",
      "address": "123, MG Road, Pune",
      "notes": null,
      "unit_count": 12,
      "occupied_count": 10,
      "vacant_count": 2,
      "archived_at": null,
      "created_at": "2026-10-01T10:00:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "per_page": 20
}
```

### POST /api/v1/properties

**Request**:
```json
{
  "name": "Ganesh Apartment",
  "address": "456, FC Road, Pune",
  "notes": "Near bus stop"
}
```

**Validation**:
- `name`: Required, 1–100 characters, unique per owner
- `address`: Optional
- `notes`: Optional

**Response** (201 Created): Full property object

### GET /api/v1/properties/{property_id}

**Response** (200 OK): Full property object with list of units

```json
{
  "id": "uuid",
  "name": "Shree Residency",
  "address": "123, MG Road, Pune",
  "units": [
    {
      "id": "uuid",
      "name": "101",
      "unit_type": "FLAT",
      "monthly_rent_paise": 800000,
      "rent_due_day": 5,
      "is_occupied": true,
      "current_tenant": {
        "id": "uuid",
        "name": "Rahul Sharma"
      }
    },
    {
      "id": "uuid",
      "name": "103",
      "unit_type": "FLAT",
      "monthly_rent_paise": 900000,
      "rent_due_day": 1,
      "is_occupied": false,
      "current_tenant": null
    }
  ]
}
```

### PATCH /api/v1/properties/{property_id}

Partial update. Only provided fields are changed.

**Request**:
```json
{
  "name": "Shree Residency (New)",
  "address": "Updated address"
}
```

**Response** (200 OK): Updated property object

### DELETE /api/v1/properties/{property_id}

Archives the property (soft delete by setting `archived_at`). All historical unit, tenant, and rent data is preserved. Archived properties are excluded from active listings by default.

**Response** (200 OK):
```json
{
  "message": "Property archived successfully",
  "archived_at": "2026-10-02T12:00:00Z"
}
```

---

## Units

### GET /api/v1/properties/{property_id}/units

List all units within a property.

**Response** (200 OK): Array of unit objects with tenant info

### POST /api/v1/properties/{property_id}/units

**Request**:
```json
{
  "name": "101",
  "unit_type": "FLAT",
  "monthly_rent_paise": 800000,
  "rent_due_day": 5,
  "notes": "Ground floor, road-facing"
}
```

**Validation**:
- `name`: Required, 1–50 characters, unique within property
- `unit_type`: Required, one of FLAT/ROOM/SHOP/OTHER
- `monthly_rent_paise`: Required, > 0
- `rent_due_day`: Required, integer 1–28
- `notes`: Optional

**Response** (201 Created): Full unit object

### PATCH /api/v1/units/{unit_id}

**Request** (partial update):
```json
{
  "monthly_rent_paise": 900000,
  "rent_due_day": 10
}
```

**Note**: Rent and due day changes apply to future rent records only.

**Response** (200 OK): Updated unit object

---

## Tenants

### GET /api/v1/tenants

List all tenants for the authenticated owner.

**Query params**:
- `property_id`: Filter by property (optional)
- `status`: ACTIVE | INACTIVE (default: ACTIVE)
- `page`, `per_page`

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Rahul Sharma",
      "phone": "9876543210",
      "email": null,
      "unit": {
        "id": "uuid",
        "name": "101",
        "property_name": "Shree Residency"
      },
      "move_in_date": "2026-06-01",
      "status": "ACTIVE",
      "current_month_rent_status": "PAID"
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 20
}
```

### POST /api/v1/tenants

**Request**:
```json
{
  "unit_id": "uuid",
  "name": "Rahul Sharma",
  "phone": "9876543210",
  "email": null,
  "move_in_date": "2026-10-01",
  "security_deposit_paise": 1600000,
  "notes": null
}
```

**Validation**:
- `unit_id`: Required, must belong to owner, must not have an active tenant
- `name`: Required, 2–100 characters
- `phone`: Required, valid phone
- `move_in_date`: Required, valid date
- `security_deposit_paise`: Optional, >= 0

**Error** (409 Conflict):
```json
{
  "detail": "Unit 101 already has an active tenant (Amit Patel). Deactivate the current tenant first.",
  "code": "UNIT_OCCUPIED"
}
```

### GET /api/v1/tenants/{tenant_id}

**Response** (200 OK): Full tenant object with rent history

```json
{
  "id": "uuid",
  "name": "Rahul Sharma",
  "phone": "9876543210",
  "unit": { "id": "uuid", "name": "101", "property_name": "Shree Residency" },
  "move_in_date": "2026-06-01",
  "security_deposit_paise": 1600000,
  "status": "ACTIVE",
  "rent_history": [
    {
      "id": "uuid",
      "month": 10,
      "year": 2026,
      "expected_amount_paise": 800000,
      "total_paid_paise": 800000,
      "due_date": "2026-10-05",
      "status": "PAID",
      "payments": [
        {
          "id": "uuid",
          "amount_paise": 800000,
          "payment_method": "CASH",
          "paid_date": "2026-10-05"
        }
      ]
    }
  ]
}
```

### PATCH /api/v1/tenants/{tenant_id}

Partial update for contact info, deposit, notes.

### POST /api/v1/tenants/{tenant_id}/deactivate

**Request**:
```json
{
  "move_out_date": "2026-10-31"
}
```

**Response** (200 OK):
```json
{
  "message": "Tenant deactivated. Unit 101 is now vacant.",
  "tenant_status": "INACTIVE",
  "unit_status": "VACANT"
}
```

---

## Rent Records

### GET /api/v1/rent

Get rent records for a specific month.

**Query params**:
- `month`: Integer 1–12 (default: current month)
- `year`: Integer (default: current year)
- `property_id`: Filter by property (optional)
- `status`: PENDING | DUE | OVERDUE | PAID | PARTIALLY_PAID (optional)

**Response** (200 OK):
```json
{
  "month": 10,
  "year": 2026,
  "summary": {
    "total_expected_paise": 16000000,
    "total_collected_paise": 14200000,
    "total_pending_paise": 1800000,
    "paid_count": 18,
    "due_count": 4,
    "overdue_count": 2
  },
  "items": [
    {
      "id": "uuid",
      "tenant_name": "Suresh Kumar",
      "unit_name": "104",
      "property_name": "Shree Residency",
      "expected_amount_paise": 1500000,
      "total_paid_paise": 0,
      "due_date": "2026-10-01",
      "status": "OVERDUE",
      "last_reminder_at": null
    }
  ]
}
```

**Side effect**: When this endpoint is called, it triggers on-demand rent record generation for the requested month for all active tenants who don't already have a rent record for that month (see ADR-002).

### GET /api/v1/rent/{rent_record_id}

Detailed view of a single rent record with all payments.

### PATCH /api/v1/rent/{rent_record_id}

Edit a rent record (e.g., adjust expected amount for a partial month, add notes).

**Request**:
```json
{
  "expected_amount_paise": 400000,
  "notes": "Prorated for half month"
}
```

### POST /api/v1/rent/{rent_record_id}/void

Void a rent record (e.g., created by mistake).

**Request**:
```json
{
  "reason": "Created by mistake - tenant hadn't moved in yet"
}
```

---

## Payments

### POST /api/v1/rent/{rent_record_id}/payments

Record a payment against a rent record.

**Request**:
```json
{
  "amount_paise": 800000,
  "payment_method": "CASH",
  "paid_date": "2026-10-05",
  "notes": "",
  "confirm_excess": false
}
```

**Validation**:
- `amount_paise`: Required, > 0
- `payment_method`: Required, one of `CASH`, `UPI`, `BANK_TRANSFER`, `OTHER`
- `paid_date`: Required, valid date, cannot be in the future
- `confirm_excess`: Optional boolean (default: false). If total payments after this transaction would exceed 2x `expected_amount_paise` and `confirm_excess` is false, returns `422 Unprocessable Entity` with code `EXCESSIVE_AMOUNT_WARNING`. When `confirm_excess` is true, the payment is recorded with landlord confirmation.

**Response** (201 Created):
```json
{
  "payment": {
    "id": "uuid",
    "amount_paise": 800000,
    "payment_method": "CASH",
    "paid_date": "2026-10-05"
  },
  "rent_record": {
    "id": "uuid",
    "expected_amount_paise": 800000,
    "total_paid_paise": 800000,
    "status": "PAID"
  }
}
```

### PATCH /api/v1/payments/{payment_id}

Edit a payment (correction).

**Request**:
```json
{
  "amount_paise": 700000,
  "notes": "Corrected amount"
}
```

### POST /api/v1/payments/{payment_id}/void

Void a payment.

**Request**:
```json
{
  "reason": "Entered by mistake"
}
```

---

## Dashboard

### GET /api/v1/dashboard/summary

**Query params**:
- `month`: Integer (default: current)
- `year`: Integer (default: current)

**Response** (200 OK):
```json
{
  "month": 10,
  "year": 2026,
  "total_expected_paise": 16000000,
  "total_collected_paise": 14200000,
  "total_pending_paise": 1800000,
  "paid_count": 18,
  "due_count": 4,
  "overdue_count": 2,
  "total_units": 27,
  "occupied_units": 24,
  "vacant_units": 3,
  "todays_due": [
    {
      "tenant_name": "Ravi Patel",
      "unit_name": "301",
      "property_name": "Shree Residency",
      "amount_paise": 1000000,
      "rent_record_id": "uuid"
    }
  ],
  "overdue_list": [
    {
      "tenant_name": "Suresh Kumar",
      "unit_name": "104",
      "property_name": "Shree Residency",
      "amount_paise": 1500000,
      "due_date": "2026-10-01",
      "rent_record_id": "uuid",
      "tenant_id": "uuid",
      "tenant_phone": "9876543210"
    }
  ],
  "recent_payments": [
    {
      "tenant_name": "Rahul Sharma",
      "amount_paise": 800000,
      "payment_method": "CASH",
      "paid_date": "2026-10-02"
    }
  ]
}
```

**Query params**:
- `month`: Optional integer (1-12, default: current month in IST)
- `year`: Optional integer (2020-2100, default: current year in IST)
- `property_id`: Optional UUID filter

**Side effect**: Triggers on-demand rent record generation for the specified month (same as GET /rent).

---

## Reminders

### POST /api/v1/rent/{rent_record_id}/reminders

Generate and record a tenant reminder for a specific rent obligation. (Also aliased as `POST /api/v1/tenants/{tenant_id}/reminders` with `rent_record_id` in body for backwards compatibility).

**Request**:
```json
{}
```

**Validation**:
- Rent record must have an unpaid balance (`total_paid_paise < expected_amount_paise`)
- Rent status must be DUE, OVERDUE, or PARTIALLY_PAID
- Cooldown: at least 24 hours since last reminder for this rent record (returns `400 Bad Request` with code `REMINDER_COOLDOWN_ACTIVE` if cooldown is active)

**Response** (200 OK):
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "rent_record_id": "uuid",
  "whatsapp_url": "https://wa.me/919876543210?text=Hi%20Suresh%2C%20your%20monthly%20rent...",
  "message": "Hi Suresh, your monthly rent of ₹15,000 for October 2026 was due on 1 October. Please make the payment at the earliest. Thank you.",
  "remaining_amount_paise": 1500000,
  "sent_at": "2026-10-02T17:30:00Z"
}
```

*Note*: If partial payment has already been recorded, `message` automatically uses the remaining balance amount (e.g. "remaining rent balance of ₹5,000").

### GET /api/v1/rent/{rent_record_id}/reminders

List reminder history recorded for a specific rent obligation.

**Response** (200 OK): List of reminder records ordered newest first.

### GET /api/v1/tenants/{tenant_id}/reminders

List all reminder history recorded across all rent obligations for a tenant.

**Response** (200 OK): List of reminder records ordered newest first.

---

## Reports

### GET /api/v1/reports/monthly

Generate read-only monthly collection report with financial aggregations, rent status counts, payment method breakdowns, and outstanding tenant lists.

**Query params**:
- `month`: Optional integer (1-12, default: current month in IST)
- `year`: Optional integer (2020-2100, default: current year in IST)
- `property_id`: Optional UUID filter

**Response** (200 OK):
```json
{
  "month": 10,
  "year": 2026,
  "summary": {
    "total_expected_paise": 5000000,
    "total_collected_paise": 3500000,
    "total_pending_paise": 1500000,
    "paid_count": 2,
    "partially_paid_count": 1,
    "due_count": 1,
    "overdue_count": 0
  },
  "payment_breakdown": {
    "cash_paise": 1500000,
    "upi_paise": 2000000,
    "bank_transfer_paise": 0,
    "other_paise": 0
  },
  "outstanding": {
    "total_count": 2,
    "total_amount_paise": 1500000,
    "tenants": [
      {
        "tenant_id": "uuid",
        "tenant_name": "Ravi Kumar",
        "property_id": "uuid",
        "property_name": "Shree Residency",
        "unit_id": "uuid",
        "unit_name": "Flat 101",
        "rent_record_id": "uuid",
        "expected_amount_paise": 1000000,
        "paid_amount_paise": 0,
        "remaining_amount_paise": 1000000,
        "status": "DUE",
        "due_date": "2026-10-05",
        "days_overdue": 0
      }
    ]
  }
}
```

---

## Authorization Rules

Every endpoint (except `/auth/*`) enforces:

1. Valid JWT token present in `Authorization: Bearer <token>`
2. `owner_id` extracted from JWT claims (never trusted from request body)
3. Requested resource must belong to the authenticated owner (traced through property → `owner_id`)
4. If resource does not exist OR belongs to another owner → **404 Not Found** (prevents resource existence leakage)

```json
{
  "detail": "Resource not found",
  "code": "NOT_FOUND"
}
```
