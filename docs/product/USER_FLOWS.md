# User Flows — RentBook

## 1. First-Time Setup

```
Owner opens app
→ Registers (email + password)
→ Logged in, sees empty dashboard
→ Taps "Add Property"
→ Enters property name and address
→ Property created, sees empty property page
→ Taps "Add Unit"
→ Enters: Unit 101, Flat, ₹8,000/month, due 5th
→ Unit created
→ Taps "Add Tenant" on Unit 101
→ Enters: Rahul Sharma, 9876543210, move-in 01 Oct 2026, deposit ₹16,000
→ Tenant assigned to Unit 101
→ Returns to dashboard
→ Dashboard now shows: Expected ₹8,000, Collected ₹0, Pending ₹8,000
```

**Key principle**: Owner should go from zero to a working rent register in under 5 minutes.

---

## 2. Monthly Rent Cycle — Normal Flow

```
Month: October 2026
Unit 101: Rahul, ₹8,000, due 5th

Oct 1 — Owner opens dashboard
       → Sees "October 2026" summary
       → Rent record for Rahul exists: ₹8,000, PENDING
       
Oct 3 — Status still PENDING (before due date)

Oct 5 — Due date arrives
       → Status becomes DUE
       → "Remind" button becomes available
       
Oct 5 — Rahul pays cash
       → Owner opens app
       → Finds Rahul (dashboard pending list or tenant page)
       → Taps "Record Payment"
       → Amount: ₹8,000 (pre-filled)
       → Method: Cash
       → Date: Today (pre-filled)
       → Confirms
       → Status becomes PAID
       → Dashboard updates: Collected +₹8,000, Pending -₹8,000
```

---

## 3. Overdue Flow

```
Month: October 2026
Unit 104: Suresh, ₹15,000, due 1st

Oct 1 — Due date
       → Status: DUE

Oct 3 — Due date passed, no payment
       → Status: OVERDUE
       → Dashboard highlights Suresh in overdue section

Oct 3 — Owner taps "Remind" on Suresh
       → WhatsApp opens with message:
         "Hi Suresh, your monthly rent of ₹15,000 for October 2026 was due on 
          1 October. Please make the payment at the earliest. Thank you."
       → Reminder timestamp recorded in system

Oct 7 — Suresh pays via UPI
       → Owner records payment: ₹15,000, UPI, paid 7 Oct
       → Status: PAID
```

---

## 4. Tenant Replacement

```
Scenario: Amit (Unit 102) is leaving, new tenant Deepak is moving in.

Step 1 — Deactivate Amit
  → Owner opens Amit's profile
  → Taps "Move Out" / "Deactivate"
  → Enters move-out date: 31 Oct 2026
  → Amit's status → INACTIVE
  → Unit 102 status → VACANT
  → Amit's historical rent records remain intact and viewable

Step 2 — Unit 102 is now vacant
  → No rent records generated for Nov 2026 onwards
  → Property page shows Unit 102 as VACANT

Step 3 — Add new tenant
  → Owner opens Unit 102
  → Taps "Add Tenant"
  → Enters: Deepak Joshi, 9876543211, move-in 15 Nov 2026, deposit ₹15,000
  → Unit 102 status → OCCUPIED
  → Rent tracking begins for Deepak from November 2026
```

**Critical**: Amit's historical data (Sep 2026 PAID, Oct 2026 PAID, etc.) must remain accessible even after deactivation.

---

## 5. Vacant Unit Flow

```
Unit 103 — no tenant assigned

Dashboard view:
  → Unit 103 does NOT appear in pending/due/overdue lists
  → Unit 103 appears in "Vacant" count

Property detail view:
  → Unit 103 shows as "VACANT" with option to "Add Tenant"

No rent records are created for vacant units.
```

---

## 6. Payment Correction

```
Scenario: Owner recorded ₹8,000 payment for Rahul but it was actually ₹7,000.

Owner opens Rahul's payment for October 2026
→ Taps "Edit"
→ Changes amount from ₹8,000 to ₹7,000
→ Adds note: "Partial payment, ₹1,000 pending"
→ Saves
→ Rent status recalculates:
   If ₹7,000 < ₹8,000 expected → Status: PARTIALLY_PAID
→ Dashboard updates accordingly
```

**Important**: The system should record that an edit was made (at minimum, an updated_at timestamp). Financial data should not be silently altered without any trace.

---

## 7. Mid-Month Tenant Join

```
Scenario: New tenant Priya moves into Unit 201 on October 15.

Owner adds Priya with move-in date Oct 15
→ For October 2026:
   → Rent record can be created manually if owner wants to charge
   → System does NOT automatically prorate
   → Owner enters the agreed amount for the partial month
   → Or owner skips October entirely
→ From November 2026 onwards:
   → Normal monthly rent records at full amount
```

**MVP approach**: No automatic proration. The owner decides what to charge for a partial month. This matches how physical registers work.

---

## 8. Rent Amount Change

```
Scenario: Unit 101 rent increases from ₹8,000 to ₹9,000 starting January 2027.

Owner edits Unit 101
→ Changes monthly rent to ₹9,000
→ Change takes effect for future rent records
→ All existing records (Oct 2026: ₹8,000, Nov 2026: ₹8,000, etc.) remain unchanged
→ January 2027 rent record: ₹9,000

Historical integrity preserved.
```

---

## 9. Dashboard Quick View

```
Owner opens app (daily usage)
→ Dashboard loads showing current month (October 2026)

╔════════════════════════════════════════╗
║  October 2026                          ║
║                                        ║
║  Expected    ₹1,60,000                 ║
║  Collected   ₹1,42,000                 ║
║  Pending     ₹18,000                   ║
║                                        ║
║  Paid: 18  │  Due: 4  │  Overdue: 2    ║
║  Occupied: 24  │  Vacant: 3            ║
╚════════════════════════════════════════╝

Overdue:
  • Suresh Kumar — Unit 104 — ₹15,000 — Due 1 Oct  [Remind]
  • Meena Gupta — Unit 205 — ₹6,000 — Due 1 Oct    [Remind]

Due Today:
  • Ravi Patel — Unit 301 — ₹10,000 — Due 2 Oct    [Remind]

Recent Payments:
  • Rahul Sharma — ₹8,000 — Cash — 2 Oct
  • Priya Desai — ₹5,000 — UPI — 1 Oct
```

---

## 10. Reminder Flow

```
Owner sees Suresh is overdue
→ Taps "Remind" button next to Suresh
→ System generates message:
   "Hi Suresh, your monthly rent of ₹15,000 for October 2026 
    was due on 1 October. Please make the payment at the earliest. 
    Thank you."
→ WhatsApp opens with Suresh's phone number and pre-filled message
→ Owner taps Send in WhatsApp
→ System records: reminder sent at 2 Oct 2026 5:30 PM
→ "Remind" button shows last reminded timestamp
```

---

## 11. Viewing Tenant History

```
Owner opens Rahul's profile
→ Sees current info:
   Unit 101, Shree Residency
   Rent: ₹8,000/month
   Move-in: 01 Jun 2026
   Deposit: ₹16,000

→ Sees rent history:
   Oct 2026 — ₹8,000 — PAID — 5 Oct — Cash
   Sep 2026 — ₹8,000 — PAID — 6 Sep — UPI
   Aug 2026 — ₹8,000 — PAID — 5 Aug — Cash
   Jul 2026 — ₹8,000 — PAID — 7 Jul — UPI
   Jun 2026 — ₹8,000 — PAID — 5 Jun — Cash
```

---

## 12. Multi-Property Navigation

```
Owner has 3 properties:
  - Shree Residency (12 units)
  - Ganesh Apartment (8 units)
  - Park View Shops (5 units)

Dashboard shows aggregate across all properties.

Owner taps "Properties" in navigation
→ Sees list:
   Shree Residency — 10 occupied, 2 vacant
   Ganesh Apartment — 7 occupied, 1 vacant
   Park View Shops — 5 occupied, 0 vacant

Owner taps "Shree Residency"
→ Sees all 12 units with status
→ Can drill into any unit/tenant
```
