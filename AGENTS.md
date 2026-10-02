# AGENTS.md — RentBook

## What Is This Product?

RentBook is a **digital rent register for Indian landlords**. It replaces physical notebooks, Excel sheets, and WhatsApp-based tracking with a simple web app. The core function is tracking who has paid rent, who hasn't, and who needs a reminder.

**Read**: [docs/product/PRODUCT_CONTEXT.md](docs/product/PRODUCT_CONTEXT.md) for full context.

---

## Core Principle

> **Keep the rent-management workflow simple. This is a digital register, not enterprise software.**

If you're about to add complexity, ask: "Would a landlord who uses a paper register understand this?"

---

## Product Hierarchy

```
Owner (authenticated user)
 └── Property (building/complex)
      └── Unit (flat/room/shop)
           └── Tenant (current occupant)
                └── Rent Record (monthly obligation)
                     └── Payment (recorded transaction)
```

**Ownership chain**: Every resource traces back to a property's `owner_id`. This is the security boundary.

---

## Architecture

```
React (Tailwind CSS)  →  FastAPI  →  PostgreSQL
     Frontend              API          Database
```

### Backend Layers

| Layer | Purpose | Rule |
|-------|---------|------|
| Routes (`app/api/`) | HTTP handling | Thin — delegate to services |
| Services (`app/services/`) | Business logic | All rules live here |
| Repositories (`app/repositories/`) | Data access | Always filter by `owner_id` |
| Models (`app/models/`) | ORM definitions | |
| Schemas (`app/schemas/`) | Request/response validation | |

**Read**: [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for full details.

---

## Critical Domain Rules

These rules are non-negotiable. Violating any of them is a bug.

1. **Owner isolation**: Owner A must NEVER see Owner B's data. Every database query for user-owned data MUST filter by `owner_id`.
2. **Rent status is computed, not stored**: Status (PAID/PARTIALLY_PAID/DUE/OVERDUE/PENDING) is calculated dynamically in ONE centralized function from `due_date`, `expected_amount_paise`, and `SUM(non_void_payments)`.
3. **Financial data is never hard-deleted**: Rent records and payments use `is_void = TRUE` for cancellation. No `DELETE FROM payments` or `DELETE FROM rent_records`.
4. **Money is stored in paise**: All monetary values are integers in paise (₹8,000 = 800000). Never use floats for money.
5. **One active tenant per unit**: A unit can have at most one tenant with `status = 'ACTIVE'`.
6. **Rent records are generated on-demand**: When dashboard or rent page is viewed, missing rent records are created for eligible active tenants (`move_in_date <= month`). No background cron jobs.
7. **Rent amount is snapshot**: When a rent record is created, it captures the unit's current rent. Changing the unit's rent does NOT update existing records.
8. **Due day is 1–28**: Strictly enforced to avoid month-length issues across all months.
9. **No duplicate rent records**: Unique constraint on `(tenant_id, month, year)`.
10. **Security deposit is strictly separate from rent**: Deposits are informational only and NEVER mixed into monthly rent expected/collected calculations.
11. **Reminders request remaining balance**: If partial payment has occurred, the reminder message requests the remaining balance (`expected - total_paid`), not the initial full amount.
12. **Historical debt settlement**: Deactivated (`INACTIVE`) tenants can still have payments recorded against their existing historical rent records.

**Read**: [docs/product/BUSINESS_RULES.md](docs/product/BUSINESS_RULES.md) for complete rules.

---

## Security Rules

1. **Every repository method that queries user-owned data MUST accept and filter by `owner_id`.**
2. **`owner_id` comes from JWT, never from request body.**
3. **Return 404 (not 403) for resources that don't belong to the user** — prevents existence leaking.
4. **Passwords are bcrypt-hashed**, never logged, never returned in API responses.
5. **No credentials in source code** — all secrets via environment variables.
6. **Input validation at API boundary** — Pydantic models with strict types, length limits, bounds checks.

**Read**: [docs/architecture/SECURITY.md](docs/architecture/SECURITY.md) for full checklist.

---

## Coding Rules

### Before Writing Code

1. **Read this file** and relevant product docs.
2. **Inspect the existing codebase** — understand current patterns, conventions, and structure.
3. **Check if similar functionality exists** — reuse, don't duplicate.
4. **Identify the smallest correct change** — avoid touching unrelated modules.

### While Writing Code

5. **Follow existing patterns** — if the codebase uses a certain structure for routes/services/repos, follow it.
6. **Keep routes thin** — no business logic in route handlers.
7. **Validate at API boundaries** — Pydantic schemas for all request/response models.
8. **Always filter by `owner_id`** — no exceptions for user-owned data.
9. **Use transactions** where multiple database writes must succeed or fail together (e.g., creating a payment and updating rent status).
10. **Handle all states in the frontend** — loading, error, empty, and success states for every data-fetching component.

### After Writing Code

11. **Write tests for business logic** — service layer tests at minimum.
12. **Verify authorization** — manually check that cross-owner access returns 404.
13. **Check for regressions** — run the full test suite.
14. **Update documentation** — if behavior changed, update the relevant doc.

### Do NOT

- ❌ Rewrite working architecture without a strong reason
- ❌ Add speculative features not in the MVP scope
- ❌ Introduce new dependencies without clear justification
- ❌ Change business rules without updating documentation
- ❌ Add complex abstractions "for future use"
- ❌ Skip authorization checks for convenience
- ❌ Use floats for monetary values
- ❌ Hard-delete financial records
- ❌ Compute rent status in multiple places
- ❌ Create long, multi-step forms in the UI

---

## UX Rules

1. **Mobile-first** — design for 360px width first.
2. **Minimal** — one primary action per screen, 3–4 nav items max.
3. **Fast** — payment recording in ≤ 3 taps.
4. **Landlord-friendly** — use "Flat 101" not "Unit #UUID". Use "₹8,000" not "800000".
5. **No enterprise patterns** — no sidebars, no breadcrumbs, no data tables with sort columns.
6. **Empty states** — every empty section has helpful guidance.
7. **Error states** — plain language errors, never stack traces.

**Read**: [docs/ux/UX_PRINCIPLES.md](docs/ux/UX_PRINCIPLES.md) for full guidelines.

---

## Testing Requirements

### Must-Test Scenarios

| Area | What to test |
|------|-------------|
| Rent status | All status transitions (PENDING→DUE→OVERDUE→PAID) |
| Rent generation | Active tenants get records; vacant units don't |
| Payment | Recording, partial, void, correction |
| Authorization | Owner A cannot access Owner B's anything |
| Dashboard | Correct aggregation of expected/collected/pending |
| Tenant lifecycle | Add, deactivate, preserve history |

### Definition of Done

A feature is complete when:
- [ ] Business logic works correctly
- [ ] API validates inputs (reject bad data)
- [ ] Authorization is enforced (owner isolation)
- [ ] Database constraints are correct
- [ ] UI handles loading/error/empty states
- [ ] Tests exist for critical behavior
- [ ] No regression in existing tests
- [ ] Documentation updated if behavior changed

**Read**: [docs/testing/TESTING_STRATEGY.md](docs/testing/TESTING_STRATEGY.md) for test specifications.

---

## Key Documentation

| Document | Path | What It Covers |
|----------|------|----------------|
| Product Context | [docs/product/PRODUCT_CONTEXT.md](docs/product/PRODUCT_CONTEXT.md) | What the product is, domain model, philosophy |
| MVP Scope | [docs/product/MVP_SCOPE.md](docs/product/MVP_SCOPE.md) | What's in/out of MVP |
| User Flows | [docs/product/USER_FLOWS.md](docs/product/USER_FLOWS.md) | Step-by-step user workflows |
| Business Rules | [docs/product/BUSINESS_RULES.md](docs/product/BUSINESS_RULES.md) | All domain rules with IDs |
| Edge Cases | [docs/product/EDGE_CASES.md](docs/product/EDGE_CASES.md) | Known edge cases and expected behavior |
| Roadmap | [docs/product/ROADMAP.md](docs/product/ROADMAP.md) | Phase 1/2/3 planning |
| Architecture | [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | System design, layers, data flow |
| Database | [docs/architecture/DATABASE.md](docs/architecture/DATABASE.md) | Schema, tables, constraints |
| API | [docs/architecture/API.md](docs/architecture/API.md) | Endpoints, request/response specs |
| Security | [docs/architecture/SECURITY.md](docs/architecture/SECURITY.md) | Auth, authorization, data protection |
| Notifications | [docs/architecture/NOTIFICATIONS.md](docs/architecture/NOTIFICATIONS.md) | Reminder strategy |
| UX Principles | [docs/ux/UX_PRINCIPLES.md](docs/ux/UX_PRINCIPLES.md) | Design guidelines |
| Information Architecture | [docs/ux/INFORMATION_ARCHITECTURE.md](docs/ux/INFORMATION_ARCHITECTURE.md) | Navigation, pages, layout |
| Architecture Decisions | [docs/decisions/ADR-001-to-004.md](docs/decisions/ADR-001-to-004.md) | Key decisions with rationale |
| Testing Strategy | [docs/testing/TESTING_STRATEGY.md](docs/testing/TESTING_STRATEGY.md) | Test approach and cases |
| Critical Flows | [docs/testing/CRITICAL_FLOWS.md](docs/testing/CRITICAL_FLOWS.md) | Flows that must always work |

---

## Agent Working Process

When assigned a task:

```
1. Read AGENTS.md (this file)
2. Read relevant product documentation for the task
3. Inspect the existing codebase — understand what exists
4. Understand existing architecture and patterns
5. Identify which modules are affected
6. Plan the smallest correct change
7. Implement
8. Write/update tests
9. Verify no regressions
10. Update documentation if behavior changed
```

**Never skip steps 1–5.** Understanding the context prevents unnecessary rewrites.
