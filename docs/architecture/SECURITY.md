# Security — RentBook

## Authentication

### Password Security

| Requirement | Implementation |
|-------------|----------------|
| Hashing algorithm | bcrypt with work factor ≥ 12 |
| Minimum password length | 8 characters |
| Password storage | Only hash stored; plaintext never persisted or logged |
| Password in responses | Never returned in any API response |

### JWT Token Security

| Requirement | Implementation |
|-------------|----------------|
| Signing algorithm | HS256 (symmetric) for MVP; RS256 for production scale |
| Access token expiry | 30 minutes |
| Refresh token expiry | 7 days |
| Token storage (Android App) | Hardware-backed keystore via `expo-secure-store` |
| Token storage (Mobile Web) | `localStorage` (or `httpOnly` cookie) |
| Token claims | `sub` (user_id), `exp`, `iat` |
| Secret key | Environment variable, minimum 32 characters, cryptographically random |
| Token rotation | Refresh token is single-use; new refresh token issued on refresh |

### Client Trust Model (Dual-Client Architecture)

> **Core Rule**: The client application (whether the Android APK or the mobile web app) is **NEVER a trusted environment**.

1. **No Embedded Secrets**: Never compile backend API secret keys, database credentials, or third-party service tokens into the Android APK or web JavaScript bundles.
2. **Identity from Token Only**: `owner_id` is extracted strictly from verified JWT claims on the server. Never accept or trust `owner_id` from client request parameters.
3. **Backend Authorization is the Boundary**: All authorization checks happen at the repository layer in FastAPI. Client-side hiding of UI buttons is a UX convenience, never a security mechanism.

---

## Authorization

### Data Isolation Model

```
Every data query MUST include owner_id filtering.

This is NOT optional. This is NOT a frontend/client concern.
This MUST be enforced at the repository/data-access layer.
```

### Implementation Pattern

```python
# CORRECT — Every repository method filters by owner_id
class PropertyRepository:
    def get_all(self, owner_id: UUID) -> list[Property]:
        return db.query(Property).filter(Property.owner_id == owner_id).all()
    
    def get_by_id(self, property_id: UUID, owner_id: UUID) -> Property:
        prop = db.query(Property).filter(
            Property.id == property_id,
            Property.owner_id == owner_id
        ).first()
        if not prop:
            raise NotFoundError()  # Returns 404, not 403 (avoid leaking existence)
        return prop

# INCORRECT — Never do this
class PropertyRepository:
    def get_by_id(self, property_id: UUID) -> Property:  # Missing owner_id!
        return db.query(Property).filter(Property.id == property_id).first()
```

### Authorization Chain for Nested Resources

For entities below property level (units, tenants, rent, payments), ownership is verified by joining back to properties:

```python
# Verifying tenant belongs to owner
tenant = (
    db.query(Tenant)
    .join(Unit, Tenant.unit_id == Unit.id)
    .join(Property, Unit.property_id == Property.id)
    .filter(
        Tenant.id == tenant_id,
        Property.owner_id == owner_id
    )
    .first()
)
```

### Key Rules

1. **Never return 403 for nonexistent resources** — return 404. This prevents attackers from discovering valid IDs.
2. **Never trust client-provided owner_id** — always extract from JWT.
3. **Never skip authorization checks for "convenience"** — even internal service calls should validate ownership.

---

## Input Validation

### API Boundary Validation

| Rule | Implementation |
|------|----------------|
| Request validation | Pydantic models with strict types |
| String length limits | All string fields have max length |
| Numeric bounds | Monetary values > 0, due day 1–28, month 1–12, year 2020–2100 |
| Email validation | Standard email format validation |
| Phone validation | Regex for Indian phone numbers |
| UUID validation | Valid UUID format for all ID parameters |
| Date validation | ISO 8601 format, logical bounds (not future for paid_date) |

### SQL Injection Prevention

- **ORM-only database access** — No raw SQL strings with user input
- SQLAlchemy parameterized queries used throughout
- No string concatenation in query building

### XSS Prevention

- React's default JSX escaping handles most cases
- No `dangerouslySetInnerHTML` unless absolutely necessary (and then sanitize)
- Content-Security-Policy headers

---

## API Security

### Rate Limiting

| Endpoint | Limit |
|----------|-------|
| POST /auth/login | 5 attempts per minute per IP |
| POST /auth/register | 3 per hour per IP |
| All other endpoints | 60 requests per minute per user |

### CORS

```
Allowed origins: [frontend domain only]
Allowed methods: GET, POST, PATCH, DELETE
Allowed headers: Authorization, Content-Type
Credentials: true
```

### HTTP Security Headers

| Header | Value |
|--------|-------|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| Strict-Transport-Security | max-age=31536000; includeSubDomains (production) |
| X-XSS-Protection | 0 (rely on CSP instead) |
| Content-Security-Policy | default-src 'self'; script-src 'self' |
| Referrer-Policy | strict-origin-when-cross-origin |

---

## Data Protection

### PII Handling

| Data | Classification | Rules |
|------|---------------|-------|
| Owner email | PII | Not exposed to other owners |
| Owner password hash | Sensitive | Never logged, never in responses |
| Tenant name | PII | Scoped to owner only |
| Tenant phone | PII | Scoped to owner only; used for reminders |
| Tenant email | PII | Scoped to owner only |
| Payment records | Financial | Never hard-deleted |

### Logging

- **Never log**: Passwords, tokens, full phone numbers, email addresses
- **Safe to log**: User IDs (UUIDs), action types, error codes, request paths
- **Mask in logs**: Phone numbers → `98765***10`, emails → `r***@example.com`

### Environment Variables

```
SECRET_KEY=<cryptographically random, 32+ chars>
DATABASE_URL=<connection string>
```

- `.env` file in `.gitignore`
- `.env.example` with placeholder values committed
- Production secrets via hosting platform's secret manager

---

## Security Checklist for Development

Every PR / feature implementation should verify:

- [ ] All database queries filter by `owner_id`
- [ ] New endpoints have authentication middleware
- [ ] Input validation uses Pydantic models
- [ ] No raw SQL with user input
- [ ] No credentials in source code or logs
- [ ] Financial data is not hard-deleted
- [ ] Error responses don't leak internal details
- [ ] New string fields have length limits
- [ ] Monetary inputs are validated (> 0, sanity bounds)
