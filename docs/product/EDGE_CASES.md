# Edge Cases — RentBook

## MVP-Required Edge Cases

These edge cases MUST be handled correctly in the MVP.

### EC-01: Tenant Joins Mid-Month

**Scenario**: Priya moves into Unit 201 on October 15.

**Expected behavior**:
- Owner adds Priya with move-in date Oct 15
- For October, the owner can manually create a rent record with whatever amount they agree upon (full month, prorated, or free)
- The system does NOT auto-prorate
- From November onwards, full monthly rent records are generated normally

**Rationale**: Auto-proration is complex and landlords handle this differently. In a physical register, they just write the agreed amount.

---

### EC-02: Tenant Leaves Mid-Month

**Scenario**: Amit is deactivated on October 20. His rent was due Oct 10.

**Expected behavior**:
- If Amit's October rent record already exists and is PAID → no change
- If Amit's October rent record exists and is unpaid → it stays as-is (owner can record partial payment or write it off by voiding)
- After deactivation, no rent records are generated for Amit from November onwards
- Unit becomes VACANT

---

### EC-03: Rent Amount Change

**Scenario**: Unit 101 rent increases from ₹8,000 to ₹9,000 starting January 2027.

**Expected behavior**:
- Owner edits Unit 101 monthly rent to ₹9,000
- All existing rent records (Oct, Nov, Dec 2026) retain ₹8,000
- New rent record for Jan 2027 will be created with ₹9,000
- Rent record amount is a snapshot; it does not change retroactively

---

### EC-04: Due Date Change

**Scenario**: Unit 101 due date changes from 5th to 10th.

**Expected behavior**:
- Owner edits Unit 101 rent_due_day to 10
- Existing rent records retain their original due dates
- New rent records will use the 10th
- Status computation uses the due date stored on each rent record, not the unit's current setting

---

### EC-05: Duplicate Rent Record Prevention

**Scenario**: Owner views October dashboard, then navigates away, then returns.

**Expected behavior**:
- The system checks if a rent record for tenant+month+year already exists before creating one
- Database has a unique constraint on (tenant_id, month, year)
- No duplicates are ever created

---

### EC-06: Vacant Unit — No Rent Generation

**Scenario**: Unit 103 is vacant in October.

**Expected behavior**:
- When October rent records are generated, Unit 103 is skipped
- No rent record exists for a vacant unit
- Dashboard calculations exclude vacant units from expected amounts

---

### EC-07: Payment Exceeds Expected Rent

**Scenario**: Owner accidentally records ₹80,000 instead of ₹8,000.

**Expected behavior**:
- System shows a warning: "Payment amount (₹80,000) is significantly more than expected rent (₹8,000). Are you sure?"
- If owner confirms, payment is recorded
- If owner cancels, they can correct the amount
- Threshold: warn if payment > 2x expected amount (BR-PAY-08)

---

### EC-08: Multiple Payments for One Month

**Scenario**: Tenant pays ₹4,000 on Oct 5 and ₹4,000 on Oct 10 (split payment).

**Expected behavior**:
- First payment: ₹4,000 recorded → status: PARTIALLY_PAID (if past due date) or PENDING (if before due date)
- Second payment: ₹4,000 recorded → total = ₹8,000 → status: PAID
- Both payments are visible in the rent record's payment history

---

### EC-09: Payment Correction

**Scenario**: Owner entered ₹8,000 but actual payment was ₹7,000.

**Expected behavior**:
- Owner edits the payment, changing amount to ₹7,000
- `updated_at` timestamp is refreshed
- Rent status recalculates based on new total
- Original amount is not preserved in MVP (full audit trail is a future enhancement)

---

### EC-10: Tenant Moving Between Units

**Scenario**: Rahul moves from Unit 101 to Unit 201 within the same property.

**Expected behavior**:
- Deactivate Rahul from Unit 101 (sets move-out date, unit becomes vacant)
- Add Rahul as a new tenant record on Unit 201 (new move-in date)
- Unit 101's historical records remain linked to the old tenant record
- Unit 201 gets a fresh rent tracking timeline
- The two tenant records may share the same name/phone but are separate database records

**Note**: In MVP, there is no explicit "transfer tenant" feature. It's done as deactivate + re-add.

---

### EC-11: Due Date of 29th, 30th, 31st

**Scenario**: Owner wants rent due on the 31st.

**Expected behavior**:
- Rent due day is restricted to 1–28 (BR-UNIT-03)
- The UI should not allow selecting 29, 30, or 31
- Validation error: "Due day must be between 1 and 28"

**Rationale**: February has 28 days. Using 29–31 would create inconsistent behavior across months. Simplest correct approach for MVP.

---

### EC-12: Owner Deletes Property with Existing Data

**Scenario**: Owner tries to delete "Shree Residency" which has tenants, rent records, and payments.

**Expected behavior**:
- Hard delete is blocked: "This property has existing records and cannot be deleted."
- Owner can archive the property instead
- Archived property is hidden from the main view but data is preserved

---

### EC-13: Recording Payment for Future Month

**Scenario**: Owner tries to record payment for November while it's still October.

**Expected behavior**:
- The rent record for November doesn't exist yet (on-demand generation)
- Owner would need to navigate to November to generate the rent record first, then record payment
- Alternatively, for MVP simplicity: only allow payment recording for existing rent records

---

### EC-14: Owner with Zero Properties

**Scenario**: Newly registered owner has no data.

**Expected behavior**:
- Dashboard shows empty state with guidance: "Welcome! Add your first property to get started."
- No errors, no blank screens
- Clear call-to-action to add a property

---

### EC-15: Timezone — IST Assumption

**Scenario**: All due date calculations.

**Expected behavior**:
- MVP assumes IST (Asia/Kolkata) for all date logic
- "Today" is determined by IST
- Due date comparisons use IST date, not UTC
- This is acceptable because the target market is Indian landlords

---

## Future Edge Cases (Not in MVP)

These are documented for awareness but do NOT need to be solved in the MVP.

| ID | Edge Case | Why Not MVP |
|----|-----------|-------------|
| EC-F01 | Tenant pays via payment gateway and system auto-records | No payment gateway in MVP |
| EC-F02 | Multiple active tenants in one unit (shared room) | Adds complexity; one tenant per unit for MVP |
| EC-F03 | Staff member manages properties on behalf of owner | No multi-role support in MVP |
| EC-F04 | Tenant disputes a recorded payment | No tenant portal in MVP |
| EC-F05 | Owner imports 50 tenants from Excel | No bulk import in MVP |
| EC-F06 | Rent in foreign currency | INR only for MVP |
| EC-F07 | Automatic rent escalation (annual increase) | Manual rent update is sufficient for MVP |
| EC-F08 | Utility billing alongside rent | Out of scope |
| EC-F09 | Maintenance deduction from rent | Out of scope |
| EC-F10 | Legal notice generation | Out of scope |
