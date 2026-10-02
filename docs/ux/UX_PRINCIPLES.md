# UX Principles — RentBook

## Design Philosophy

> **The physical rent register is the mental model.**

Every design decision should be evaluated against: "Is this simpler than the paper register?"

If a digital feature is harder to use than writing in a notebook, it has failed.

---

## Core UX Principles

### 1. Instant Clarity

The owner should understand their rent collection status **within 5 seconds** of opening the app.

- Large, readable numbers for Expected / Collected / Pending
- Color-coded status indicators (green = paid, red = overdue, orange = due)
- No interpretation needed — the data speaks for itself

### 2. Minimal Cognitive Load

- One primary action per screen
- No more than 3–4 navigation items
- No nested menus
- Terminology the landlord already uses (not technical jargon)
- "Flat 101" not "Unit #UID-2847-a3"

### 3. Speed Over Features

The most frequent actions must be the fastest:

| Action | Target | How |
|--------|--------|-----|
| Check rent status | < 2 seconds | Dashboard loads instantly |
| Record a payment | < 3 taps | Tenant → Record Payment → Confirm |
| Send a reminder | < 2 taps | Remind button → WhatsApp opens |

### 4. Mobile-First

- 80%+ of usage will be on mobile phones
- All layouts designed for 360px–414px width first
- Touch-friendly tap targets (minimum 44x44px)
- No hover-dependent interactions
- Bottom navigation for primary actions
- Large text (minimum 14px body, 24px+ for monetary amounts)

### 5. Forgiving

- Undo/edit for all recorded data
- Confirmation dialogs for destructive actions
- Clear error messages in plain language
- Empty states with helpful guidance, not blank screens

### 6. Landlord Language

| ✅ Use | ❌ Avoid |
|--------|---------|
| Flat 101 | Unit #UUID |
| ₹8,000 | 800000 paise |
| Rent due | Payment obligation pending |
| Remind | Send notification |
| Paid | Payment status: COMPLETED |
| Vacant | Occupancy status: UNOCCUPIED |

---

## Visual Design Guidelines

### Color System

| Purpose | Color | Usage |
|---------|-------|-------|
| Paid / Success | Green (#22C55E) | Paid status, collected amount |
| Overdue / Alert | Red (#EF4444) | Overdue status, urgent items |
| Due / Warning | Amber (#F59E0B) | Due today, pending items |
| Vacant | Gray (#9CA3AF) | Vacant units, inactive |
| Primary Action | Blue (#3B82F6) | CTA buttons, links |
| Background | Neutral (#F9FAFB / #FFFFFF) | Page backgrounds |

### Typography

- **Monetary amounts**: Bold, large (24–32px), tabular numbers
- **Status labels**: Semi-bold, color-coded, uppercase
- **Names**: Regular weight, 16px
- **Secondary text**: Light, 14px, muted color
- **Font**: System font stack (fast loading, familiar)

### Status Indicators

```
● PAID        → Green badge/chip
● DUE         → Amber badge/chip  
● OVERDUE     → Red badge/chip
● PENDING     → Gray badge/chip
● VACANT      → Gray outline badge
```

### Cards & Lists

- Tenant/rent items displayed as cards on mobile
- Clear visual hierarchy: Name → Amount → Status → Action
- Adequate spacing between items (no cramped lists)
- Subtle shadows for depth, not heavy borders

---

## Anti-Patterns — What NOT to Do

### ❌ Dashboard Overload
- No pie charts, bar graphs, or complex visualizations
- No "analytics" section in MVP
- Just the numbers that matter

### ❌ Long Forms
- No multi-step wizards
- Add Tenant form: 4–5 fields maximum
- Add Property: 2 fields (name + address)
- Record Payment: 3 fields (amount + method + date)

### ❌ Excessive Filtering
- No advanced filter panels
- Simple property dropdown if needed
- Status filter (Paid/Due/Overdue) if needed
- Nothing more in MVP

### ❌ Technical Terminology
- No UUIDs visible to users
- No "entity", "record", "instance" language
- No HTTP error codes displayed
- Errors in plain language: "Something went wrong. Please try again."

### ❌ Unnecessary Animations
- No page transition animations
- No skeleton screens for sub-second loads
- No confetti, celebrations, or gamification
- Subtle loading spinners only when genuinely loading

### ❌ Enterprise UI Patterns
- No sidebar navigation
- No breadcrumbs
- No tabs within tabs
- No data tables with sortable columns
- No bulk selection checkboxes

---

## Empty States

Every section that can be empty must have a helpful empty state:

| Section | Empty State Message |
|---------|-------------------|
| Properties | "No properties yet. Add your first property to get started." + [Add Property] button |
| Units | "No units in this property. Add your first unit." + [Add Unit] button |
| Tenants | "No tenants yet. Add a tenant to start tracking rent." |
| Rent (month) | "No rent records for this month." |
| Payment history | "No payments recorded yet." |
| Dashboard | "Welcome! Add a property and tenants to see your rent dashboard." |

---

## Loading & Error States

### Loading
- Show a simple spinner or skeleton for data that takes > 500ms
- Don't block the entire page; load sections independently where possible

### Errors
- API errors: "Something went wrong. Please try again."
- Network errors: "You appear to be offline. Check your connection."
- Validation errors: Inline, next to the field, in red
- Never show stack traces or technical error details to users

---

## Accessibility (Minimum)

- Sufficient color contrast (WCAG AA)
- All buttons and links are keyboard-accessible
- Form labels are properly associated with inputs
- Focus indicators are visible
- Text is not conveyed by color alone (icons/labels supplement color)
