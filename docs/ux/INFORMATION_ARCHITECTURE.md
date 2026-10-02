# Information Architecture — RentBook

## Navigation Structure

### Primary Navigation (Bottom Bar — Mobile)

```
┌─────────┬─────────┬─────────┬─────────┐
│  Home   │Properties│  Rent   │  More   │
│   🏠    │    🏢   │   💰    │   ⋯    │
└─────────┴─────────┴─────────┴─────────┘
```

| Tab | Purpose | Primary Question Answered |
|-----|---------|--------------------------|
| **Home** (Dashboard) | Monthly overview, action center | "How is my collection going?" |
| **Properties** | Property & unit management | "What do I own? Who lives where?" |
| **Rent** | Monthly rent tracking | "Who has paid and who hasn't?" |
| **More** | Settings, profile, help | "How do I manage my account?" |

### Why Not a Tenants Tab?

Tenants are accessed contextually — through properties (unit → tenant) or through rent records (rent → tenant). A separate top-level Tenants tab adds navigation without adding clarity. Tenants can be listed under "More" if needed.

---

## Page Hierarchy

```
Dashboard (/)
├── Monthly summary cards
├── Overdue list → [Remind] [Record Payment]
├── Due today list → [Remind] [Record Payment]
└── Recent payments

Properties (/properties)
├── Property list → tap to view
│
└── Property Detail (/properties/:id)
    ├── Property info (name, address)
    ├── Unit list with occupancy
    │   ├── Occupied unit → tenant name, rent status
    │   └── Vacant unit → [Add Tenant]
    │
    ├── Add Unit (/properties/:id/units/new)
    │
    └── Unit Detail (/units/:id)
        ├── Unit info (type, rent, due day)
        ├── Current tenant → [View Tenant]
        └── [Add Tenant] (if vacant)

Tenants
├── Tenant Detail (/tenants/:id)
│   ├── Contact info
│   ├── Unit & property info
│   ├── Rent history (monthly)
│   │   └── Per-month: amount, status, payment details
│   ├── [Record Payment] (for current/due months)
│   ├── [Remind] (if due/overdue)
│   └── [Deactivate / Move Out]
│
└── Add Tenant (/tenants/new?unit_id=xxx)
    └── Name, phone, move-in date, deposit

Rent (/rent)
├── Month selector (← Oct 2026 →)
├── Summary: Expected / Collected / Pending
├── Filter: All | Paid | Due | Overdue
├── Rent record list
│   └── Per record: tenant, unit, amount, status, [Pay] [Remind]
│
└── Record Payment (/rent/:id/pay)
    └── Amount (pre-filled), method, date, notes → [Confirm]

More (/settings)
├── Profile (name, email, phone)
├── All Tenants list
├── About / Help
└── Logout
```

---

## Page Specifications

### Dashboard Page

**Purpose**: The owner's home screen. Answers "How is my collection going this month?"

```
┌────────────────────────────────────┐
│  October 2026                      │
│                                    │
│  ┌──────────┐ ┌──────────┐        │
│  │ Expected │ │ Collected│        │
│  │₹1,60,000 │ │₹1,42,000│        │
│  └──────────┘ └──────────┘        │
│  ┌──────────┐                     │
│  │ Pending  │                     │
│  │ ₹18,000  │                     │
│  └──────────┘                     │
│                                    │
│  Paid: 18  Due: 4  Overdue: 2     │
│  Occupied: 24  Vacant: 3          │
│                                    │
│  ── Overdue ──────────────────     │
│  Suresh Kumar  Unit 104  ₹15,000  │
│  Due 1 Oct          [Remind] [Pay]│
│                                    │
│  ── Due Today ────────────────     │
│  Ravi Patel  Unit 301  ₹10,000    │
│  Due 2 Oct           [Remind] [Pay]│
│                                    │
│  ── Recent Payments ──────────     │
│  Rahul Sharma  ₹8,000  Cash  2Oct │
│  Priya Desai   ₹5,000  UPI   1Oct │
└────────────────────────────────────┘
```

### Record Payment Page

**Purpose**: The fastest path to recording a payment. This is the most common action.

```
┌────────────────────────────────────┐
│  Record Payment                    │
│                                    │
│  Tenant: Rahul Sharma              │
│  Unit: 101, Shree Residency       │
│  Rent: ₹8,000 (October 2026)      │
│                                    │
│  Amount     ┌──────────────┐       │
│             │ ₹ 8,000      │       │
│             └──────────────┘       │
│                                    │
│  Method     ○ Cash  ○ UPI         │
│             ○ Bank  ○ Other       │
│                                    │
│  Date       ┌──────────────┐       │
│             │ 02 Oct 2026  │       │
│             └──────────────┘       │
│                                    │
│  Notes      ┌──────────────┐       │
│             │ (optional)   │       │
│             └──────────────┘       │
│                                    │
│  ┌─────────────────────────────┐   │
│  │      Confirm Payment        │   │
│  └─────────────────────────────┘   │
└────────────────────────────────────┘
```

Key UX decisions:
- Amount is pre-filled with expected rent
- Method defaults to last used method (or Cash)
- Date defaults to today
- One big "Confirm" button
- Success → toast message + back to previous screen

---

## Navigation Patterns

### Getting to Record Payment (Most Common Action)

**Path 1**: Dashboard → [Pay] button on overdue/due tenant (fastest)

**Path 2**: Rent tab → Find tenant → [Pay] button

**Path 3**: Properties → Property → Unit → Tenant → [Record Payment]

Path 1 should be the most common. The dashboard surfaces the tenants who need attention.

### Getting to Remind

**Path 1**: Dashboard → [Remind] button on overdue/due tenant (fastest)

**Path 2**: Rent tab → Find tenant → [Remind]

---

## Information Density Guidelines

| Screen | Information shown |
|--------|------------------|
| Dashboard | 3 summary numbers + 2 lists (overdue, recent) |
| Property list | Name, unit counts, occupancy |
| Property detail | All units with status |
| Unit detail | Unit info, current tenant |
| Tenant detail | Contact, rent history |
| Rent overview | Month summary + rent record list |
| Payment form | 4 fields |

**Rule**: If a screen has more than 3 distinct information sections, it's too complex.
