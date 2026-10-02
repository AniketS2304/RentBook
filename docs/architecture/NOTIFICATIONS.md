# Notifications Architecture — RentBook

## MVP Approach: WhatsApp Deep Links

### How It Works

1. Owner sees a tenant with DUE or OVERDUE rent
2. Owner taps "Remind" button
3. System generates a pre-filled WhatsApp URL
4. WhatsApp app opens on the owner's phone with the message ready to send
5. Owner taps Send in WhatsApp
6. System records that a reminder was initiated

### WhatsApp Deep Link Format

```
https://wa.me/{phone_number}?text={encoded_message}
```

Example:
```
https://wa.me/919876543210?text=Hi%20Rahul%2C%20your%20monthly%20rent%20of%20%E2%82%B98%2C000%20for%20October%202026%20is%20due%20on%205%20October.%20Please%20make%20the%20payment%20by%20the%20due%20date.%20Thank%20you.
```

### Message Templates

#### Before/On Due Date
```
Hi {tenant_name}, your monthly rent of ₹{amount} for {month} {year} is due on {due_date}. Please make the payment by the due date. Thank you.
```

#### After Due Date (Overdue)
```
Hi {tenant_name}, your monthly rent of ₹{amount} for {month} {year} was due on {due_date}. Please make the payment at the earliest. Thank you.
```

### Rules

| Rule | Description |
|------|-------------|
| Eligibility | Only tenants with DUE or OVERDUE rent |
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
