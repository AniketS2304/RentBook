# Testing Strategy — RentBook

## Philosophy

> Test business correctness, not implementation details. Prioritize tests that catch real bugs over tests that satisfy coverage metrics.

## Test Pyramid

```
        ┌─────────┐
        │  E2E    │  ← Few: critical user flows only
        ├─────────┤
        │  API    │  ← Moderate: endpoint validation & auth
        ├─────────┤
        │ Service │  ← Core: business logic tests
        ├─────────┤
        │  Unit   │  ← Foundation: utilities, helpers, pure functions
        └─────────┘
```

## Testing Tools & Environments

| Component | Tool / Environment | Focus |
|-----------|-------------------|-------|
| **Backend Core** (`apps/api`) | pytest + SQLAlchemy | Unit tests for pure business rules, rent status computation, and migrations |
| **Backend API** (`apps/api`) | pytest + httpx (`TestClient`) | Endpoint contracts, Pydantic validation, status codes, owner isolation |
| **Backend Database** (`apps/api`) | PostgreSQL test container/instance | Transaction rollback tests, partial unique constraint enforcement |
| **Android App** (`apps/mobile`) | React Native Testing Library + Jest | Component rendering, touch events, form inputs, native back behavior |
| **Android Device Testing** | Standalone APK on physical Android device | EAS build installation, native keyboard avoidance, WhatsApp deep-link launching |
| **Mobile Web App** (`apps/web`) | Vitest + React Testing Library | Responsive viewport rendering, touch interactions, safe area layout |
| **Mobile Safari Testing** | iPhone physical device / Safari responsive mode | Viewport height handling (`100dvh`), notch padding, web WhatsApp redirect |
| **E2E Testing** | Playwright (optional Phase 2 tool) | Automated cross-browser end-to-end flows (deferred for initial MVP) |

---

## Critical Test Cases

### 1. Rent Status Computation

The rent status function is the most important piece of business logic. It MUST be thoroughly tested.

```python
# test_rent_status.py

def test_status_pending_before_due_date():
    """Rent with no payment before due date → PENDING"""

def test_status_due_on_due_date():
    """Rent with no payment on due date → DUE"""

def test_status_overdue_after_due_date():
    """Rent with no payment after due date → OVERDUE"""

def test_status_paid_full_payment():
    """Rent with payment >= expected → PAID"""

def test_status_paid_overpayment():
    """Rent with payment > expected → PAID (not error)"""

def test_status_partially_paid_before_due():
    """Partial payment before or on due date → PARTIALLY_PAID"""

def test_status_overdue_with_partial_payment():
    """Partial payment where due date has passed → OVERDUE (unpaid balance remains)"""

def test_status_excludes_voided_payments():
    """Voided payments should not count toward total paid"""

def test_status_multiple_payments_summed():
    """Multiple payments sum correctly to determine status"""
```

### 2. Rent Record Generation

```python
# test_rent_generation.py

def test_generates_records_for_active_tenants():
    """On-demand generation creates records for all active tenants"""

def test_skips_vacant_units():
    """Vacant units (no active tenant) do not get rent records"""

def test_skips_inactive_tenants():
    """Inactive tenants do not get new rent records"""

def test_no_duplicate_records():
    """Calling generation twice for same month creates no duplicates"""

def test_uses_current_rent_amount():
    """Rent record amount = unit's current monthly_rent_paise at creation"""

def test_correct_due_date():
    """Due date = year-month-unit.rent_due_day"""

def test_mid_month_tenant_gets_record():
    """Tenant added mid-month gets a record on next generation"""
```

### 3. Payment Recording

```python
# test_payment.py

def test_record_payment_success():
    """Valid payment is recorded and linked to rent record"""

def test_payment_updates_rent_status():
    """Recording full payment changes status to PAID"""

def test_partial_payment():
    """Payment less than expected → status reflects partial"""

def test_payment_amount_must_be_positive():
    """Zero or negative payment amounts are rejected"""

def test_payment_date_not_future():
    """Payment with future date is rejected"""

def test_payment_exceeds_sanity_check():
    """Payment > 2x expected triggers warning (but can be overridden)"""

def test_void_payment():
    """Voided payment is excluded from total calculations"""

def test_edit_payment():
    """Edited payment updates amount and updated_at"""
```

### 4. Authorization / Data Isolation

```python
# test_authorization.py

def test_owner_sees_only_own_properties():
    """Owner A cannot see Owner B's properties"""

def test_owner_cannot_access_other_owners_unit():
    """Accessing another owner's unit returns 404"""

def test_owner_cannot_access_other_owners_tenant():
    """Accessing another owner's tenant returns 404"""

def test_owner_cannot_record_payment_for_other_owner():
    """Recording payment on another owner's rent record returns 404"""

def test_unauthenticated_request_returns_401():
    """Request without valid JWT returns 401"""

def test_expired_token_returns_401():
    """Request with expired JWT returns 401"""

# These tests MUST create two owners with separate data and verify
# that cross-access is blocked at every endpoint.
```

### 5. Dashboard Calculations

```python
# test_dashboard.py

def test_expected_amount_sums_all_rent_records():
    """Total expected = sum of all rent record expected amounts for month"""

def test_collected_amount_sums_payments():
    """Total collected = sum of non-voided payments for month's rent records"""

def test_pending_is_expected_minus_collected():
    """Pending = Expected - Collected"""

def test_overdue_count():
    """Overdue count = rent records past due with insufficient payment"""

def test_vacant_count():
    """Vacant count = units without active tenants"""

def test_dashboard_scoped_to_owner():
    """Dashboard only includes authenticated owner's data"""
```

### 6. Tenant Lifecycle

```python
# test_tenant_lifecycle.py

def test_add_tenant_to_vacant_unit():
    """Adding tenant to vacant unit succeeds"""

def test_add_tenant_to_occupied_unit_fails():
    """Adding tenant to occupied unit returns 409"""

def test_deactivate_tenant():
    """Deactivating tenant sets INACTIVE and vacates unit"""

def test_deactivated_tenant_history_preserved():
    """After deactivation, rent records still accessible"""

def test_new_tenant_after_deactivation():
    """New tenant can be added to unit after previous tenant deactivated"""
```

### 7. Property & Unit Operations

```python
# test_property.py

def test_create_property():
def test_archive_property():
def test_archived_property_hidden_from_list():
def test_cannot_delete_property_with_financial_data():

# test_unit.py
def test_create_unit():
def test_unit_name_unique_within_property():
def test_due_day_must_be_1_to_28():
def test_rent_change_does_not_affect_existing_records():
```

### 8. Reminders

```python
# test_reminders.py

def test_reminder_generates_correct_message():
    """Message includes tenant name, amount, month, due date"""

def test_reminder_uses_remaining_balance_on_partial_payment():
    """Message specifies remaining balance (not full rent) if partial payment made"""

def test_reminder_generates_whatsapp_url():
    """URL is correctly formatted with phone and encoded message"""

def test_reminder_cooldown():
    """Cannot send another reminder within 24 hours"""

def test_reminder_only_for_due_or_overdue():
    """Cannot remind for PAID or PENDING rent"""
```

---

## Test Data Strategy

### Test Fixtures

Create reusable test fixtures:

```python
@pytest.fixture
def owner_a():
    """Owner A with properties, units, tenants, and rent data"""

@pytest.fixture
def owner_b():
    """Owner B with separate properties (for isolation tests)"""

@pytest.fixture
def property_with_mixed_status():
    """Property with PAID, DUE, OVERDUE, and VACANT units"""
```

### Database Strategy

- Use a separate PostgreSQL database for tests
- Each test runs in a transaction that is rolled back
- Migrations applied before test suite runs

---

## What NOT to Test (in MVP)

- CSS/styling
- UI pixel precision
- Third-party library internals
- Database driver behavior
- Framework behavior (FastAPI routing, Pydantic validation)

---

## Definition of Done — Test Requirements

A feature is complete when:

| Requirement | Description |
|-------------|-------------|
| ✅ Business logic tested | Service layer tests for all business rules |
| ✅ API validation tested | Invalid inputs return proper errors |
| ✅ Authorization tested | Owner isolation verified |
| ✅ Edge cases covered | Documented edge cases have tests |
| ✅ No regressions | Existing tests still pass |
