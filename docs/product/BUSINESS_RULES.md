# Business Rules — RentBook

## 1. Ownership & Data Isolation

| Rule | Description |
|------|-------------|
| BR-OWN-01 | Every property belongs to exactly one owner. |
| BR-OWN-02 | Every unit belongs to exactly one property. |
| BR-OWN-03 | Every tenant record belongs to the owner (via unit → property → owner). |
| BR-OWN-04 | Owner A must never see, modify, or access Owner B's data. |
| BR-OWN-05 | All API queries must filter by authenticated owner_id. This is enforced at the backend, not just the frontend. |

## 2. Properties

| Rule | Description |
|------|-------------|
| BR-PROP-01 | A property must have a name. Address is optional but recommended. |
| BR-PROP-02 | A property can have zero or more units. |
| BR-PROP-03 | Archiving a property soft-deletes it; it remains in the database with an `archived_at` timestamp. |
| BR-PROP-04 | An archived property's units and historical data remain accessible for viewing but no new rent records are generated. |
| BR-PROP-05 | A property cannot be hard-deleted if it has any rent or payment history. |
| BR-PROP-06 | Property names do not need to be unique globally, but should be unique per owner for clarity. |

## 3. Units

| Rule | Description |
|------|-------------|
| BR-UNIT-01 | A unit must have a name/number, type, monthly rent, and rent due day. |
| BR-UNIT-02 | Unit types: `FLAT`, `ROOM`, `SHOP`, `OTHER`. |
| BR-UNIT-03 | Rent due day is an integer 1–28. Days 29–31 are not allowed to avoid month-length issues. |
| BR-UNIT-04 | A unit can have at most one **active** tenant at any time. |
| BR-UNIT-05 | Occupancy status is derived: if an active tenant exists → `OCCUPIED`, otherwise → `VACANT`. |
| BR-UNIT-06 | A unit's monthly rent can be changed; the change applies to future rent records only. Existing records are not affected. |
| BR-UNIT-07 | Units within a property should have unique names/numbers. |
| BR-UNIT-08 | Deleting a unit is not allowed if it has any historical tenant or rent data. It can be archived. |

## 4. Tenants

| Rule | Description |
|------|-------------|
| BR-TEN-01 | A tenant must have a name and phone number. Email is optional. |
| BR-TEN-02 | A tenant is assigned to exactly one unit at a time. |
| BR-TEN-03 | A tenant has a move-in date. Move-out date is set when deactivated. |
| BR-TEN-04 | Deactivating a tenant sets their status to `INACTIVE` and their unit becomes `VACANT`. |
| BR-TEN-05 | Deactivating a tenant does NOT delete their rent or payment history. |
| BR-TEN-06 | An inactive tenant's historical records remain viewable. |
| BR-TEN-07 | The same phone number may exist for different tenants (e.g., a tenant moves to a different unit/property over time). |
| BR-TEN-08 | Security deposit is recorded as an informational monetary amount. It is NOT considered rent and is NEVER included in monthly expected/collected rent calculations. |
| BR-TEN-09 | A tenant cannot be assigned to an already-occupied unit. The existing tenant must be deactivated first. |
| BR-TEN-10 | A tenant entity represents a specific tenancy. If a tenant moves to a different unit, a new tenant record is created for the new unit. |

## 5. Rent Records

| Rule | Description |
|------|-------------|
| BR-RENT-01 | A rent record represents one tenant's rent obligation for one calendar month. |
| BR-RENT-02 | There must be at most one rent record per tenant per month (unique constraint: `tenant_id` + `month` + `year`). |
| BR-RENT-03 | Rent records are created on-demand when the owner views a specific month's data (see ADR-002). Only tenants whose `move_in_date` is on or before the requested month, and who were not moved out before the start of that month, are eligible. |
| BR-RENT-04 | Rent records are only created for active tenants occupying a unit. Vacant units do not generate rent records. |
| BR-RENT-05 | The rent amount on a record is snapshot at creation time from the unit's current monthly rent. Landlords can manually adjust `expected_amount_paise` (e.g. for mid-month joins) via edit. |
| BR-RENT-06 | Once a rent record is created, its expected amount is independent of future unit rent changes. |
| BR-RENT-07 | Rent records should not be hard-deleted. They can be voided/cancelled with a reason (`is_void = TRUE`). Voided records are excluded from calculations. |

### Rent Status Rules

Rent status is **computed dynamically** in a single centralized function from:
- `expected_amount_paise`
- `total_paid_paise` (sum of non-voided payments)
- `due_date`
- `today` (current date in IST)

| Status | Condition |
|--------|-----------|
| `PAID` | `total_paid >= expected_amount` (obligation fully satisfied) |
| `PARTIALLY_PAID` | `0 < total_paid < expected_amount` AND `today <= due_date` (partial payment received, due date not passed) |
| `OVERDUE` | `total_paid < expected_amount` AND `today > due_date` (due date passed with an unpaid balance, whether ₹0 or partial) |
| `DUE` | `total_paid == 0` AND `today == due_date` (due today, no payment received yet) |
| `PENDING` | `total_paid == 0` AND `today < due_date` (upcoming, due date in the future) |

| Rule | Description |
|------|-------------|
| BR-RENT-08 | Rent status is **computed**, not stored. It is calculated dynamically whenever rent records are queried. |
| BR-RENT-09 | Status computation is centralized in one function. Multiple conflicting calculations are forbidden. |
| BR-RENT-10 | The due date for a rent record = the unit's `rent_due_day` within the record's month/year (`YYYY-MM-DD`). |
| BR-RENT-11 | Any rent record where `total_paid < expected_amount` AND `today > due_date` is classified as overdue in dashboard counts, overdue lists, and reminder triggers. |

## 6. Payments

| Rule | Description |
|------|-------------|
| BR-PAY-01 | A payment is always linked to a specific rent record. |
| BR-PAY-02 | A rent record can have multiple payments (to support partial payments, installments, and split payments). |
| BR-PAY-03 | Payment amount must be > 0. |
| BR-PAY-04 | Payment method must be one of: `CASH`, `UPI`, `BANK_TRANSFER`, `OTHER`. |
| BR-PAY-05 | Payment date defaults to today but can be backdated (not forward-dated beyond today). |
| BR-PAY-06 | Payments cannot be hard-deleted. They can be voided (`is_void = TRUE`) with an optional reason. |
| BR-PAY-07 | Editing a payment updates amount/method/date and records `updated_at`. |
| BR-PAY-08 | Total payments for a rent record exceeding 2x the expected rent amount triggers a warning (`confirm_excess` required to record). |
| BR-PAY-09 | Recording or voiding a payment immediately recalculates the rent record's effective status and dashboard totals. |
| BR-PAY-10 | Deactivated (`INACTIVE`) tenants can still have payments recorded against their existing historical rent records (e.g. past overdue settlements). |

## 7. Reminders

| Rule | Description |
|------|-------------|
| BR-REM-01 | Reminders are available only for rent records with an unpaid balance where status is DUE or OVERDUE (`today >= due_date`). |
| BR-REM-02 | Sending a reminder opens WhatsApp with a pre-filled message. The system records the reminder timestamp. |
| BR-REM-03 | Cooldown: Minimum 24 hours between reminders for the same rent record. |
| BR-REM-04 | Reminder messages include: tenant name, remaining unpaid balance (`expected - total_paid`), month, due date. |
| BR-REM-05 | The system does not auto-send reminders. All reminders are owner-initiated. |

## 8. Dashboard

| Rule | Description |
|------|-------------|
| BR-DASH-01 | Dashboard shows data for the current month by default. |
| BR-DASH-02 | All dashboard figures are computed across all owner's properties unless filtered. |
| BR-DASH-03 | "Expected" = sum of expected_amount for all rent records this month. |
| BR-DASH-04 | "Collected" = sum of all payments against this month's rent records. |
| BR-DASH-05 | "Pending" = Expected - Collected (minimum 0). |
| BR-DASH-06 | Vacant units are counted but do not contribute to expected/collected amounts. |

## 9. Data Integrity

| Rule | Description |
|------|-------------|
| BR-INT-01 | Financial records (rent records, payments) are never hard-deleted. |
| BR-INT-02 | When a tenant is deactivated, their rent and payment history remains. |
| BR-INT-03 | When a unit's rent is changed, existing rent records retain their original amount. |
| BR-INT-04 | All monetary values are stored as integers in paise (1 rupee = 100 paise) to avoid floating-point issues. Displayed as rupees in the UI. |
| BR-INT-05 | Month/year combinations are stored explicitly (not derived from timestamps) to avoid timezone ambiguity. |
| BR-INT-06 | All entities have `created_at` and `updated_at` timestamps. |
