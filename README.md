# RentBook 📖

> A digital rent register for landlords and property owners in India.

RentBook replaces physical registers, paper notebooks, Excel sheets, and scattered WhatsApp chats with a simple, reliable, mobile-friendly digital register.

---

## 🎯 What Problem Does This Solve?

Small and mid-size landlords with 5–100 rental units constantly face the question:
> **"Who has paid, who has not paid, and who do I need to remind?"**

RentBook gives instant clarity:
- **Instant visibility**: Expected vs. Collected vs. Pending rent at a glance.
- **Fast payment recording**: Record a payment in under 3 taps/clicks.
- **Overdue tracking & reminders**: One-tap pre-filled WhatsApp reminder messages.
- **Zero fluff**: No complex accounting, ERP systems, or society management features in MVP.

---

## 📁 Repository Structure & Documentation

All product definitions, architectural design decisions, and agent guidelines are thoroughly documented:

```text
├── AGENTS.md                   # Core guidelines & domain rules for AI coding agents
├── docs/
│   ├── product/
│   │   ├── PRODUCT_CONTEXT.md  # Domain model, target persona, core philosophy
│   │   ├── MVP_SCOPE.md        # Explicit in-scope & out-of-scope capabilities
│   │   ├── USER_FLOWS.md       # 12 step-by-step user workflows & wireframes
│   │   ├── BUSINESS_RULES.md   # Domain rules (BR-OWN, BR-RENT, BR-PAY, etc.)
│   │   ├── EDGE_CASES.md       # Edge cases (mid-month join, vacancy, rent changes)
│   │   └── ROADMAP.md          # 3-phase rollout roadmap
│   ├── architecture/
│   │   ├── ARCHITECTURE.md     # FastAPI + React + PostgreSQL system design
│   │   ├── DATABASE.md         # Full schema, constraints, indexes & queries
│   │   ├── API.md              # RESTful API specifications & validation
│   │   ├── SECURITY.md         # Data isolation, JWT auth, security checklist
│   │   └── NOTIFICATIONS.md    # WhatsApp deep-link notifications strategy
│   ├── ux/
│   │   ├── UX_PRINCIPLES.md    # Landlord-first mobile design principles
│   │   └── INFORMATION_ARCHITECTURE.md # Navigation, screens & wireframes
│   ├── decisions/
│   │   └── ADR-001-to-004.md   # Architectural Decision Records (ADRs)
│   └── testing/
│       ├── TESTING_STRATEGY.md # Test pyramid & comprehensive test cases
│       └── CRITICAL_FLOWS.md   # Critical flows & regression checklist
```

---

## 🛠️ Tech Stack (Target Implementation)

- **Frontend**: React (Vite) + Tailwind CSS (Mobile-first)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (SQLAlchemy + Alembic)
- **Deployment**: Docker Compose + Nginx

---

## 📜 Agent Guidelines

If you are an AI coding assistant or developer contributing to this repo, **read [`AGENTS.md`](./AGENTS.md) before writing any code.**
