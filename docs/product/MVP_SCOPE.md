# MVP Scope — RentBook

## What Is In the MVP

The MVP delivers exactly one thing well: **a digital rent register**.

---

## Feature Set

### 1. Authentication

| Capability | Details |
|-----------|---------|
| Owner registration | Email + password |
| Owner login | Email + password, returns JWT |
| Session management | JWT with refresh token |
| Data isolation | All data scoped to authenticated owner |

No social login, no magic links, no OTP in MVP. Keep it simple.

### 2. Properties

| Capability | Details |
|-----------|---------|
| Create property | Name, address, notes |
| Edit property | Update name, address, notes |
| View properties | List all owner's properties |
| View property detail | Property info + list of units |
| Archive property | Soft-delete; hides from active view |

**Example properties**: "Shree Residency", "Ganesh Apartment", "Building A"

### 3. Units

| Capability | Details |
|-----------|---------|
| Create unit | Unit name/number, type, monthly rent, rent due day |
| Edit unit | Update details; rent changes apply to future records only |
| View units | List units within a property |
| Unit types | Flat, Room, Shop, Other |
| Occupancy status | Occupied / Vacant (derived from active tenant) |

**Example**: Unit 101 → Flat → ₹8,000/month → Due on 5th

### 4. Tenants

| Capability | Details |
|-----------|---------|
| Add tenant | Name, phone, email (optional), assigned unit, move-in date, security deposit |
| Edit tenant | Update contact info, security deposit |
| Deactivate tenant | Mark as inactive, set move-out date, unit becomes vacant |
| View tenant | Tenant info + rent history |
| View all tenants | List across all properties, filterable by property |

**Minimal tenant info** — no Aadhaar, PAN, or other identity documents in MVP.

### 5. Rent Tracking

| Capability | Details |
|-----------|---------|
| Rent record creation | On-demand when owner views a month (see ADR-002) |
| View monthly rent | All rent records for a given month |
| Rent statuses | PENDING → DUE → OVERDUE → PAID |
| Due date logic | Based on unit's rent_due_day |
| Rent history | Per-tenant monthly history |

### 6. Payment Recording

| Capability | Details |
|-----------|---------|
| Record payment | Select tenant → enter amount → select method → confirm |
| Payment methods | Cash, UPI, Bank Transfer, Other |
| Edit payment | Correct amount, method, date |
| Payment date | Defaults to today, can be backdated |
| Payment notes | Optional free-text |

**No payment gateway.** The app records that payment was received, not the actual money transfer.

### 7. Dashboard

| Element | Description |
|---------|-------------|
| Total expected | Sum of all rent due this month |
| Total collected | Sum of all payments received this month |
| Pending amount | Expected minus collected |
| Overdue count | Rent records past due date and unpaid |
| Occupancy | Occupied vs vacant unit counts |
| Today's due | Rent due today |
| Recent payments | Last 10 payments recorded |
| Overdue list | Tenants with overdue rent |

### 8. Reminders

| Capability | Details |
|-----------|---------|
| Identify remindable tenants | Due today, due soon, overdue |
| Send reminder | WhatsApp deep link with pre-filled message |
| Reminder message | Template with tenant name, amount, due date |
| Reminder tracking | Record that reminder was sent (timestamp) |

**No automated messaging in MVP.** Owner manually taps "Remind" → WhatsApp opens with pre-filled message.

### 9. Vacancy Management

| Capability | Details |
|-----------|---------|
| View vacant units | Filter/view across all properties |
| Vacancy display | Shown on property detail page |
| No rent generation | Vacant units do not generate rent records |

### 10. Client Platforms (Dual-Client Scope)

Both clients provide the exact same core functional workflow against the shared FastAPI backend:

#### A. Android Native App (`apps/mobile` - Primary)
- Built with React Native, Expo, TypeScript, NativeWind, Expo Router.
- Distributed directly as a standalone APK (`RentBook.apk`) via EAS Build.
- Features: Authentication, Dashboard, Properties/Units CRUD, Tenant CRUD & Deactivation, Rent Tracking, Payment Recording (≤ 3 taps), Payment Edit/Void, Tenant Rent History, Native WhatsApp Reminder trigger, Vacant units view, Settings/Logout.
- Native UX: Android back button/gesture navigation, native keyboard handling, native deep-linking.

#### B. Mobile Web App (`apps/web` - Secondary / iPhone Safari)
- Built with React, Vite, TypeScript, Tailwind CSS.
- Targeted at iPhone users opening RentBook in Safari, and browser check-ins.
- Features: Complete parity with Android MVP workflows.
- Mobile Web UX: Safe area padding (`env(safe-area-inset-*)`), mobile touch targets, responsive bottom navigation.

---

## What Is NOT in the MVP

> **These features are explicitly excluded from the MVP.** They must NOT influence architecture decisions or code complexity.

| Excluded Feature | Reason |
|-----------------|--------|
| iOS App Store build | iPhone users use Mobile Web in MVP; native iOS compilation is deferred to Phase 2 |
| Google Play Store listing | Initial landlord validation uses direct APK distribution via EAS Build |
| Online payment gateway (Razorpay, Stripe) | Complexity; landlords collect payments externally |
| Full accounting / ledger system | Not needed for rent tracking |
| GST / tax compliance | Out of scope for rent register |
| Maintenance / repair requests | Different domain |
| Complaint management | Different domain |
| Society / association management | Different product |
| Visitor management | Different product |
| Electricity / water billing | Future feature |
| Legal agreement management | Future feature |
| Property / tenant marketplace | Different product |
| AI chatbot | Unnecessary complexity |
| Complex analytics / BI dashboards | Simple summary is enough |
| Advanced CRM | Not needed |
| Subscription / billing for SaaS | Free for MVP; monetize later |
| Multi-level staff permissions | Owner-only access in MVP |
| Complex messaging (WhatsApp API, SMS gateway) | WhatsApp deep links are sufficient |
| Tenant-facing portal | Owner-only in MVP |
| Multi-language support | English only in MVP |
| Multi-currency support | INR only |
| Bulk import from Excel | Future feature |
| Receipt generation / PDF export | Future feature |

---

## MVP Success Criteria

The MVP is successful when a real landlord can:

1. ✅ Register and log in
2. ✅ Add their properties and units
3. ✅ Add tenants to units
4. ✅ See which rent is pending, due, or overdue for the current month
5. ✅ Record a payment in under 10 seconds (≤ 3 taps)
6. ✅ View a tenant's payment history
7. ✅ Send a WhatsApp reminder to a tenant with remaining balance
8. ✅ See vacant units at a glance
9. ✅ Install and run the Android APK on a real Android phone (or access via iPhone Safari)

If these 9 things work reliably, the MVP is complete.
