# Notifications Architecture — RentBook

## MVP Approach: WhatsApp Deep Links

### How It Works

1. Landlord sees a tenant with DUE or OVERDUE rent in either the **Android app** or **Mobile Web**.
2. Landlord taps the "Remind" button.
3. Client issues `POST /api/v1/rent/{id}/reminders` to FastAPI backend:
   - Backend validates eligibility (unpaid balance, `today >= due_date`)
   - Backend enforces 24-hour cooldown
   - Backend records reminder audit timestamp
   - Backend returns formatted WhatsApp URL with pre-filled message (dynamically inserting remaining balance)
4. Client launches WhatsApp:
   - **Android Native App**: Calls React Native `Linking.openURL(whatsapp_url)` (or `whatsapp://send?phone=...&text=...`), seamlessly switching to the WhatsApp Android app.
   - **Mobile Web (Safari / Browser)**: Calls `window.open(whatsapp_url, '_blank')`, prompting iOS/browser to open WhatsApp.
5. Landlord confirms by tapping "Send" in WhatsApp.
6. Client UI shows cooldown indicator ("Reminded 2h ago").

### WhatsApp Deep Link Format

```
https://wa.me/{phone_number}?text={encoded_message}
```

Example:
```
https://wa.me/919876543210?text=Hi%20Rahul%2C%20your%20monthly%20rent%20of%20%E2%82%B98%2C000%20for%20October%202026%20is%20due%20on%205%20October.%20Please%20make%20the%20payment%20by%20the%20due%20date.%20Thank%20you.
```

### Message Templates

#### Before/On Due Date (No Payment Made)
```
Hi {tenant_name}, your monthly rent of ₹{amount} for {month} {year} is due on {due_date}. Please make the payment by the due date. Thank you.
```

#### After Due Date (Overdue - No Payment Made)
```
Hi {tenant_name}, your monthly rent of ₹{amount} for {month} {year} was due on {due_date}. Please make the payment at the earliest. Thank you.
```

#### Partial Payment Made (Remaining Balance Due/Overdue)
```
Hi {tenant_name}, your remaining rent balance of ₹{remaining_amount} for {month} {year} was due on {due_date}. Please clear the remaining balance at the earliest. Thank you.
```

### Rules

| Rule | Description |
|------|-------------|
| Eligibility | Only rent records with an outstanding balance (`total_paid < expected_amount`) and where `today >= due_date` (DUE or OVERDUE) |
| Accurate Balance | If partial payment exists, the reminder message explicitly mentions the remaining balance (`expected - total_paid`), not the initial total rent |
| Cooldown | Minimum 24 hours between reminders for the same rent record |
| Owner-initiated | System never sends messages automatically |
| Recording | System records reminder timestamp; delivery is not guaranteed since WhatsApp is external |
| Phone required | Reminder only available if tenant has a phone number |

### What the System Tracks

| Field | Value |
|-------|-------|
| tenant_id | Who was reminded |
| rent_record_id | For which rent |
| sent_at | When the remind button was tapped |
| channel | "WHATSAPP" |
| message | The actual message text |

**Note**: The system records that the owner *initiated* a reminder. It cannot confirm whether the message was actually delivered via WhatsApp (since it's a deep link, not an API call).

---

## Reminder Visibility in UI

### Dashboard
- Overdue tenants show a "Remind" button
- Due-today tenants show a "Remind" button
- If reminded within 24 hours: button shows "Reminded 2h ago" (disabled)

### Tenant Detail Page
- Shows reminder history for the current rent record
- "Last reminded: 2 Oct, 5:30 PM"

---

## Future Notification Strategy (Not in MVP)

### Phase 2: WhatsApp Business API
- Automated reminders on due date
- Automated overdue reminders (e.g., 3 days after due date)
- Delivery confirmation
- Requires WhatsApp Business verification

### Phase 2: SMS
- Fallback for tenants without WhatsApp
- Requires SMS gateway integration (MSG91, Twilio)

### Phase 3: Email
- Monthly rent summary to tenants
- Payment receipt emails

### Phase 3: Push Notifications
- Owner notifications for upcoming due dates
- Requires mobile app or PWA

### Future Reminder Rules (Configurable)

| Trigger | Default | Configurable |
|---------|---------|-------------|
| Days before due date | 2 days | Yes |
| On due date | Yes | Yes |
| Days after due date (overdue) | 3 days | Yes |
| Max reminders per month | 3 | Yes |
| Auto-send vs manual | Manual | Yes |

**These future features must NOT be built into the MVP.** The MVP supports only manual WhatsApp deep-link reminders.
