# Product Context — RentBook

## What Is RentBook?

RentBook is a **digital rent register for landlords and property owners** in India. It replaces physical registers, notebooks, Excel sheets, and WhatsApp-based tracking with a simple, reliable, mobile-first product.

## The Problem

Small and mid-size landlords in India manage rent collection using:

- **Physical registers** — prone to loss, damage, and manual errors
- **Notebooks** — no structure, hard to review history
- **Excel sheets** — cumbersome on mobile, no multi-device access
- **WhatsApp messages** — scattered, no summary view, no history

These methods fail to answer the single most important question:

> **"Who has paid, who has not paid, and who do I need to remind?"**

## The Solution

RentBook provides a **minimal digital rent register** that lets a landlord:

1. Register their properties and units (flats, rooms, shops)
2. Record tenant information
3. Track monthly rent obligations
4. Record payments quickly
5. See a clear dashboard of collection status
6. Send payment reminders to tenants

## Platform & Target Clients

RentBook is designed strictly as a **mobile-first product**:

- **Primary Experience — Android Native App**: Built with React Native and Expo, distributed directly to early landlords as a standalone APK via EAS Build. This is where the core real-world landlord usage takes place.
- **Secondary Experience — Mobile Web**: Built with React and Vite, specifically designed for mobile screens (primarily iPhone users accessing via Safari) and browser check-ins.
- **Unified Backend**: A single FastAPI + PostgreSQL REST API powers both clients, guaranteeing identical business rules and zero logic duplication.

This is NOT a desktop-first SaaS dashboard. Whether accessed via Android APK or iPhone Safari, the mental model is a smartphone-first digital register.

## Target User

**Primary user**: A landlord or property owner who:

- Owns 1–10 properties
- Has 5–100 rental units total
- Is comfortable using a smartphone (WhatsApp-level comfort)
- May not be technically sophisticated
- Wants to see rent status at a glance
- Values simplicity over features

**The user is NOT**:

- A property management company with hundreds of properties
- A real estate developer
- A housing society manager (initially)
- A tenant looking for rental listings

## Product Philosophy

### Principle 1: Simple beats feature-rich
The application should do fewer things extremely well rather than many things poorly.

### Principle 2: The physical rent register is the mental model
Every screen and interaction should feel like a better version of the paper register, not like enterprise software.

### Principle 3: Payment recording must be extremely fast
The most frequent action — marking rent as paid — should take no more than 3 taps/clicks.

### Principle 4: Financial history should never be casually destroyed
Rent records and payment history are financial data. Edits and corrections are allowed, but silent data loss is not.

### Principle 5: Security and owner data isolation are mandatory
Even for a small app, one owner must never see another owner's data.

### Principle 6: Build for real landlords, not developers
Language, terminology, and workflows should match what landlords already understand.

### Principle 7: Validate with real users before expanding the product
No speculative features. Expand only based on real user feedback.

## Domain Model

```
Owner (User)
 ├── Property A (e.g., "Shree Residency")
 │    ├── Unit 101 (Flat, ₹8,000/month, due 5th)
 │    │     └── Tenant: Rahul Sharma
 │    │            ├── Oct 2026 — ₹8,000 — PAID (5 Oct)
 │    │            ├── Sep 2026 — ₹8,000 — PAID (6 Sep)
 │    │            └── Aug 2026 — ₹8,000 — PAID (5 Aug)
 │    ├── Unit 102 (Flat, ₹7,500/month, due 10th)
 │    │     └── Tenant: Amit Patel
 │    │            ├── Oct 2026 — ₹7,500 — PENDING
 │    │            └── Sep 2026 — ₹7,500 — PAID (10 Sep)
 │    ├── Unit 103 (Flat, ₹9,000/month, due 1st)
 │    │     └── VACANT
 │    └── Unit 104 (Shop, ₹15,000/month, due 1st)
 │          └── Tenant: Suresh Kumar
 │                 └── Oct 2026 — ₹15,000 — OVERDUE
 │
 └── Property B (e.g., "Ganesh Apartment")
      ├── Room 1 (₹5,000/month, due 5th)
      │     └── Tenant: Priya Desai
      └── Room 2 (₹4,500/month, due 5th)
            └── VACANT
```

## Core Question the App Must Answer

At any moment, the landlord should be able to open the app and immediately understand:

| Question | Where to find the answer |
|----------|-------------------------|
| How much rent should I collect this month? | Dashboard — Total Expected |
| How much have I collected? | Dashboard — Total Collected |
| Who hasn't paid? | Dashboard — Pending list |
| Who is overdue? | Dashboard — Overdue list |
| Who do I need to contact? | Dashboard — Reminders |
| What is a tenant's payment history? | Tenant detail page |
| Which units are vacant? | Property detail page |

## Currency & Locale

- Primary currency: **Indian Rupee (₹ / INR)**
- Date format: **DD MMM YYYY** (e.g., 05 Oct 2026)
- Language: **English** (Hindi planned for future)
- Timezone: **IST (Asia/Kolkata)** for MVP (single timezone)
