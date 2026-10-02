# Database Design — RentBook

## Design Principles

1. **Monetary values stored in paise** (integer) — 1 rupee = 100 paise. ₹8,000 = 800000 paise.
2. **Soft deletes for financial data** — Rent records and payments are never hard-deleted.
3. **Explicit month/year** — Stored as integers, not derived from timestamps.
4. **owner_id on properties** — All ownership chains from property → unit → tenant → rent → payment.
5. **Timestamps on everything** — `created_at`, `updated_at` on all tables.
6. **UUIDs for primary keys** — Avoids sequential ID enumeration attacks.

## Entity Relationship Diagram

```
┌──────────┐       ┌───────────┐       ┌──────────┐
│  users   │──1:N──│ properties│──1:N──│  units   │
└──────────┘       └───────────┘       └────┬─────┘
                                            │ 1:N
                                       ┌────▼─────┐
                                       │ tenants  │
                                       └────┬─────┘
                                            │ 1:N
                                    ┌───────▼────────┐
                                    │  rent_records  │
                                    └───────┬────────┘
                                            │ 1:N
                                       ┌────▼─────┐
                                       │ payments │
                                       └──────────┘
                                       
                                    ┌────────────────┐
                                    │   reminders    │
                                    └────────────────┘
```

## Tables

### users

The application owner (landlord).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | |
| email | VARCHAR(255) | NOT NULL, UNIQUE | Login email |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| full_name | VARCHAR(100) | NOT NULL | Owner's display name |
| phone | VARCHAR(15) | NULL | Owner's phone |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active status |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**: `idx_users_email` (UNIQUE on email)

---

### properties

A building or property owned by a user.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| owner_id | UUID | FK → users.id, NOT NULL | Property owner |
| name | VARCHAR(100) | NOT NULL | "Shree Residency" |
| address | TEXT | NULL | Full address |
| notes | TEXT | NULL | Owner's notes |
| archived_at | TIMESTAMPTZ | NULL | NULL = active, set = archived |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**:
- `idx_properties_owner_id` (owner_id)
- `idx_properties_owner_active` (owner_id, archived_at) — for filtering active properties

**Unique constraints**: `uq_properties_owner_name` UNIQUE `(owner_id, name) WHERE archived_at IS NULL` — active property names unique per owner

---

### units

A rentable unit within a property (flat, room, shop).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| property_id | UUID | FK → properties.id, NOT NULL | Parent property |
| name | VARCHAR(50) | NOT NULL | "101", "Room 1", "Shop A" |
| unit_type | VARCHAR(20) | NOT NULL, CHECK IN ('FLAT','ROOM','SHOP','OTHER') | |
| monthly_rent_paise | INTEGER | NOT NULL, CHECK > 0 | Rent in paise |
| rent_due_day | INTEGER | NOT NULL, CHECK BETWEEN 1 AND 28 | Day of month rent is due |
| notes | TEXT | NULL | |
| archived_at | TIMESTAMPTZ | NULL | NULL = active |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**:
- `idx_units_property_id` (property_id)

**Unique constraints**: `uq_units_property_name` UNIQUE `(property_id, name) WHERE archived_at IS NULL` — active unit names unique within property

---

### tenants

A person renting a unit. One record per tenancy (if tenant moves, a new record is created).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| unit_id | UUID | FK → units.id, NOT NULL | Assigned unit |
| name | VARCHAR(100) | NOT NULL | Tenant's full name |
| phone | VARCHAR(15) | NOT NULL | Primary contact |
| email | VARCHAR(255) | NULL | Optional email |
| move_in_date | DATE | NOT NULL | |
| move_out_date | DATE | NULL | Set on deactivation |
| security_deposit_paise | INTEGER | NOT NULL, DEFAULT 0 | Informational deposit amount in paise (not counted as rent) |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'ACTIVE', CHECK IN ('ACTIVE','INACTIVE') | |
| notes | TEXT | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**:
- `idx_tenants_unit_id` (unit_id)
- `idx_tenants_unit_active` (unit_id, status) — for finding active tenant of a unit
- `idx_tenants_status` (status)

**Application-level constraint**: At most one ACTIVE tenant per unit (enforced via partial unique index or application logic).

**Partial unique index**: `uq_tenants_unit_active` UNIQUE (unit_id) WHERE status = 'ACTIVE'

---

### rent_records

A monthly rent obligation for a tenant.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| tenant_id | UUID | FK → tenants.id, NOT NULL | |
| unit_id | UUID | FK → units.id, NOT NULL | Denormalized for query convenience |
| month | INTEGER | NOT NULL, CHECK BETWEEN 1 AND 12 | Calendar month |
| year | INTEGER | NOT NULL, CHECK BETWEEN 2020 AND 2100 | Calendar year |
| expected_amount_paise | INTEGER | NOT NULL, CHECK > 0 | Snapshot of rent at creation |
| due_date | DATE | NOT NULL | Computed: year-month-due_day |
| notes | TEXT | NULL | |
| is_void | BOOLEAN | NOT NULL, DEFAULT FALSE | Voided records excluded from calculations |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**:
- `idx_rent_records_tenant_id` (tenant_id)
- `idx_rent_records_unit_id` (unit_id)
- `idx_rent_records_month_year` (month, year)
- `idx_rent_records_due_date` (due_date)

**Unique constraints**: `uq_rent_records_tenant_month` (tenant_id, month, year) — one rent record per tenant per month

**Note on status**: Rent status (PENDING, DUE, OVERDUE, PAID, PARTIALLY_PAID) is **computed** from:
- `due_date` vs today
- `expected_amount_paise` vs sum of payments
- Status is NOT stored as a column. It is calculated in the service layer.

---

### payments

Individual payment against a rent record.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| rent_record_id | UUID | FK → rent_records.id, NOT NULL | |
| amount_paise | INTEGER | NOT NULL, CHECK > 0 | Payment amount in paise |
| payment_method | VARCHAR(20) | NOT NULL, CHECK IN ('CASH','UPI','BANK_TRANSFER','OTHER') | |
| paid_date | DATE | NOT NULL | When payment was received |
| notes | TEXT | NULL | |
| is_void | BOOLEAN | NOT NULL, DEFAULT FALSE | Voided payments excluded from totals |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**:
- `idx_payments_rent_record_id` (rent_record_id)
- `idx_payments_paid_date` (paid_date)

---

### reminders

Record of reminders sent to tenants.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| tenant_id | UUID | FK → tenants.id, NOT NULL | |
| rent_record_id | UUID | FK → rent_records.id, NOT NULL | Which rent this reminder is for |
| sent_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When reminder was triggered |
| channel | VARCHAR(20) | NOT NULL, DEFAULT 'WHATSAPP' | Reminder channel |
| message | TEXT | NOT NULL | The message that was sent |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**:
- `idx_reminders_tenant_id` (tenant_id)
- `idx_reminders_rent_record_id` (rent_record_id)

---

## Ownership Chain for Authorization

To verify that an owner has access to any entity, trace back to `properties.owner_id`:

```
Payment → rent_record_id → RentRecord → unit_id → Unit → property_id → Property → owner_id
Reminder → tenant_id → Tenant → unit_id → Unit → property_id → Property → owner_id
```

Every repository method that accesses data must join back to `properties.owner_id` and filter by the authenticated user's ID.

## Computed Fields (Not Stored)

| Field | Computation |
|-------|------------|
| Unit occupancy | `EXISTS(tenant WHERE unit_id = unit.id AND status = 'ACTIVE')` |
| Rent status | Function of `due_date`, `expected_amount_paise`, `SUM(payments.amount_paise)`, `today` |
| Dashboard totals | Aggregation queries over rent_records + payments for a given month/year |

## Migration Strategy

- Use Alembic for database migrations
- Each migration has an upgrade and downgrade path
- Migrations are version-controlled in `alembic/versions/`
- Never modify a deployed migration; create a new one

## Sample Data Flow

```sql
-- Find all overdue rent for an owner in October 2026
SELECT rr.*, t.name as tenant_name, u.name as unit_name, p.name as property_name,
       COALESCE(SUM(pay.amount_paise) FILTER (WHERE pay.is_void = FALSE), 0) as total_paid_paise
FROM rent_records rr
JOIN tenants t ON rr.tenant_id = t.id
JOIN units u ON rr.unit_id = u.id
JOIN properties p ON u.property_id = p.id
LEFT JOIN payments pay ON pay.rent_record_id = rr.id
WHERE p.owner_id = :owner_id
  AND rr.month = 10
  AND rr.year = 2026
  AND rr.is_void = FALSE
  AND rr.due_date < CURRENT_DATE
GROUP BY rr.id, t.name, u.name, p.name
HAVING COALESCE(SUM(pay.amount_paise) FILTER (WHERE pay.is_void = FALSE), 0) < rr.expected_amount_paise;
```
