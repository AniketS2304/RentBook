# Critical Flows — RentBook

## Purpose

This document lists the most important user flows that MUST work correctly at all times. These flows represent the core value of the application. A regression in any of these flows is a critical bug.

---

## Flow 1: First-Time Setup

**Steps**:
1. Register new account (email + password)
2. Create first property
3. Add first unit to property
4. Add first tenant to unit
5. Dashboard shows expected rent for current month

**Verify**:
- User can register and login
- Property appears in properties list
- Unit appears in property detail
- Tenant is linked to unit
- Dashboard shows correct expected amount (≠ 0)
- Empty states are replaced with real data

---

## Flow 2: Record Payment (Happy Path)

**Steps**:
1. Dashboard shows tenant with DUE or OVERDUE rent
2. Owner taps Pay on the tenant
3. Payment form shows pre-filled amount
4. Owner selects payment method
5. Owner confirms payment
6. Rent status changes to PAID
7. Dashboard collected amount increases

**Verify**:
- Amount pre-fills correctly
- Payment is saved
- Rent status transitions to PAID
- Dashboard totals update immediately
- Success feedback shown

---

## Flow 3: Overdue Detection

**Steps**:
1. Active tenant with rent_due_day in the past for current month
2. No payment recorded
3. Dashboard loads

**Verify**:
- Tenant appears in overdue section
- Status shows OVERDUE (red indicator)
- Overdue count is correct
- Remind button is available

---

## Flow 4: Send Reminder

**Steps**:
1. Tenant has OVERDUE rent
2. Owner taps Remind
3. WhatsApp opens with pre-filled message
4. System records reminder

**Verify**:
- WhatsApp URL is correctly formatted
- Message contains correct tenant name, amount, due date
- Reminder timestamp is recorded
- Cooldown prevents immediate re-remind

---

## Flow 5: Tenant Replacement

**Steps**:
1. Deactivate existing tenant (set move-out date)
2. Unit becomes vacant
3. Add new tenant to the now-vacant unit
4. New rent tracking begins

**Verify**:
- Old tenant status = INACTIVE
- Old tenant history preserved
- Unit shows VACANT after deactivation
- No error adding new tenant to unit
- New tenant gets rent record for current month (on next view)

---

## Flow 6: Data Isolation

**Steps**:
1. Owner A creates property, unit, tenant
2. Owner B creates property, unit, tenant
3. Owner A logs in

**Verify**:
- Owner A sees ONLY their own properties
- Owner A sees ONLY their own tenants
- Owner A sees ONLY their own rent records
- Owner A cannot access Owner B's data via URL manipulation
- API returns 404 (not 403) for cross-owner access attempts

---

## Flow 7: Month Transition

**Steps**:
1. October rent records exist (mix of PAID/OVERDUE)
2. November begins
3. Owner opens dashboard

**Verify**:
- November rent records are generated for active tenants
- October records remain unchanged
- Dashboard shows November data by default
- October data still accessible

---

## Flow 8: Vacant Unit Handling

**Steps**:
1. Unit has no active tenant
2. Dashboard/rent page loads

**Verify**:
- No rent record generated for vacant unit
- Vacant unit counted in vacancy statistics
- Vacant unit does not appear in pending/overdue lists
- "Add Tenant" option available on vacant unit

---

## Flow 9: Android Standalone APK Installation & Execution

**Steps**:
1. Build standalone APK via EAS Build (`eas build -p android --profile preview/production`)
2. Transfer APK file to a physical Android device (via WhatsApp, USB, or direct download link)
3. Install APK on device (allowing install from unknown source if prompted)
4. Launch RentBook app on Android
5. Log in with registered landlord credentials
6. Perform core operations: view dashboard, record payment, tap Remind

**Verify**:
- APK builds and packages without bundling errors
- App launches cleanly on real Android hardware without crashes
- API base URL resolves to remote backend (no development `localhost` or `10.0.2.2` hardcoded in build)
- Login session persists across app close and re-launch via `expo-secure-store`
- Android hardware/gesture back button behaves predictably across stack screens
- WhatsApp launches natively with pre-filled message when Remind is tapped
- Native keyboard does not obscure form submit buttons

---

## Flow 10: Mobile Web (iPhone Safari) Execution & Viewport Usability

**Steps**:
1. Open mobile web URL in iPhone Safari (or mobile Chrome)
2. Log in with landlord credentials
3. Navigate between Home, Properties, Rent, and Settings tabs
4. Open Record Payment form and enter data
5. Trigger a WhatsApp reminder
6. Refresh the browser on an inner page

**Verify**:
- Application renders within mobile viewport width (360px–414px) without horizontal scrolling
- Top notch and bottom home-indicator bars are properly padded via `env(safe-area-inset-*)`
- Dynamic mobile toolbars do not obscure content or break layout (`100dvh` viewport handling)
- Page refresh retains authentication state without unexpected redirect to login
- Tap targets are comfortably accessible for touch (minimum 44x44px)
- WhatsApp opens correctly via web deep link (`https://wa.me/...`) in a new tab/app prompt

---

## Regression Checklist

Before any release or APK build, verify:

- [ ] Flow 1: New user can set up from scratch
- [ ] Flow 2: Payment recording works end-to-end (≤ 3 taps)
- [ ] Flow 3: Overdue tenants are correctly identified
- [ ] Flow 4: WhatsApp reminder generates correct URL with remaining balance
- [ ] Flow 5: Tenant replacement preserves history
- [ ] Flow 6: Owner A cannot see Owner B's data (404 enforced)
- [ ] Flow 7: New month generates correct rent records on-demand
- [ ] Flow 8: Vacant units are excluded from rent generation
- [ ] Flow 9: Android APK installs and runs on physical Android phone
- [ ] Flow 10: Mobile Web works on iPhone Safari with proper safe areas and session persistence
