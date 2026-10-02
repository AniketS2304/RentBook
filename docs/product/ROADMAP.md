# Product Roadmap — RentBook

## Phase 1 — MVP (Current)

> **Goal**: A working digital rent register that replaces paper/Excel/WhatsApp.

| Feature | Priority | Status |
|---------|----------|--------|
| Owner registration & login | P0 | Planned |
| Property CRUD | P0 | Planned |
| Unit CRUD | P0 | Planned |
| Tenant management | P0 | Planned |
| Rent record tracking | P0 | Planned |
| Payment recording | P0 | Planned |
| Dashboard (summary view) | P0 | Planned |
| WhatsApp reminder (deep link) | P1 | Planned |
| Rent history per tenant | P0 | Planned |
| Vacancy view | P1 | Planned |
| Android Native App (React Native / Expo APK) | P0 | Planned |
| Mobile Web App (React / Vite for Safari) | P0 | Planned |

**Success metric**: 5 real landlords using the app for at least 1 full month.

**Estimated scope**: 4–6 weeks of development.

---

## Phase 2 — Validated Improvements

> **Goal**: Improve based on real user feedback from Phase 1.

| Feature | Description |
|---------|-------------|
| iOS Native App | Compile iOS IPA from existing React Native / Expo codebase |
| App Store & Play Store | Publish to Google Play Store and Apple App Store |
| WhatsApp Business API | Automated reminders (requires business verification) |
| SMS notifications | For tenants without WhatsApp |
| Export to Excel/PDF | Monthly reports, payment receipts |
| Receipt generation | Digital rent receipt for tenants |
| Staff roles | Allow a manager/agent to manage properties on owner's behalf |
| Tenant portal | Read-only view for tenants to see their payment history |
| Bulk import | Import tenants/units from Excel |
| Better reporting | Monthly/quarterly collection reports with charts |
| Search & filters | Search tenants, filter by property/status |
| Multi-property dashboard | Per-property summary view |

**Prerequisite**: At least 10 active users providing feedback.

---

## Phase 3 — Product Expansion

> **Goal**: Expand into adjacent use cases only if validated by user demand.

| Feature | Description |
|---------|-------------|
| Maintenance requests | Tenants can report issues |
| Utility billing | Electricity, water tracking |
| Agreement management | Lease/rental agreement storage |
| Payment links | Send UPI/payment links to tenants |
| Advanced analytics | Trends, occupancy rates, revenue projections |
| Accounting integration | Export to Tally, Zoho, etc. |
| Hindi/regional language support | Multilingual UI |
| Subscription plans | Freemium model for monetization |
| Multi-tenant units | Shared rooms/PG accommodation |

**Prerequisite**: At least 50 active users and clear demand signal.

---

## Architecture Guardrails

> **Critical**: Future roadmap features must NOT influence MVP architecture decisions.

1. Do NOT build abstractions "in case we need them later"
2. Do NOT add database columns for Phase 2/3 features
3. Do NOT create unused API endpoints
4. Do NOT add configuration for features that don't exist
5. Build the simplest correct thing now; refactor when needed

The only concession to future planning:
- Use clean separation of concerns (so adding features later doesn't require rewriting everything)
- Use proper data modeling (so schema migrations are manageable)
- Don't hard-delete financial data (so audit trails can be added later)
