# RentBook 📖

> A digital rent register for landlords and property owners in India.

RentBook replaces physical registers, paper notebooks, Excel sheets, and scattered WhatsApp chats with a simple, reliable, mobile-first digital register.

---

## 📱 Mobile-First Architecture

RentBook provides a native mobile experience for Android landlords along with a lightweight mobile web client for iPhone users:

```text
                    RentBook Backend
                  FastAPI + PostgreSQL
                         │
               ┌─────────┴─────────┐
               │                   │
               ▼                   ▼
        Android Mobile App     Mobile Web
        React Native + Expo    React + Vite
        TypeScript             TypeScript
               │                   │
               ▼                   ▼
          Direct APK          iPhone Safari /
         Distribution         Mobile Browser
```

---

## 🎯 What Problem Does This Solve?

Small and mid-size landlords with 5–100 rental units constantly face the question:
> **"Who has paid, who has not paid, and who do I need to remind?"**

RentBook gives instant clarity:
- **Instant visibility**: Expected vs. Collected vs. Pending rent at a glance.
- **Fast payment recording**: Record a payment in under 3 taps/clicks.
- **Overdue tracking & reminders**: One-tap pre-filled WhatsApp reminder messages with dynamic balance calculation.
- **Zero fluff**: No complex accounting, ERP systems, or society management features in MVP.

---

## 📁 Repository Structure & Documentation

```text
RentBook/
├── apps/
│   ├── mobile/                 # Android native app (React Native, Expo, TypeScript, NativeWind)
│   ├── web/                    # Mobile web app (React, Vite, TypeScript, Tailwind CSS)
│   └── api/                    # Backend REST API (FastAPI, Python, SQLAlchemy, PostgreSQL)
├── docs/
│   ├── product/
│   │   ├── PRODUCT_CONTEXT.md  # Domain model, target persona, core philosophy
│   │   ├── MVP_SCOPE.md        # Explicit in-scope & out-of-scope capabilities
│   │   ├── USER_FLOWS.md       # 12 step-by-step user workflows & wireframes
│   │   ├── BUSINESS_RULES.md   # Domain rules (BR-OWN, BR-RENT, BR-PAY, etc.)
│   │   ├── EDGE_CASES.md       # Edge cases (mid-month join, vacancy, rent changes)
│   │   └── ROADMAP.md          # 3-phase rollout roadmap
│   ├── architecture/
│   │   ├── ARCHITECTURE.md     # Dual-client + FastAPI system design
│   │   ├── PLATFORM_STRATEGY.md# Android APK & iPhone Safari architecture
│   │   ├── DATABASE.md         # Full schema, constraints, indexes & queries
│   │   ├── API.md              # RESTful API specifications & validation
│   │   ├── SECURITY.md         # Data isolation, JWT auth, security checklist
│   │   └── NOTIFICATIONS.md    # WhatsApp deep-link notifications strategy
│   ├── ux/
│   │   ├── UX_PRINCIPLES.md    # Landlord-first mobile design principles
│   │   └── INFORMATION_ARCHITECTURE.md # Navigation, screens & wireframes
│   ├── decisions/
│   │   ├── ADR-001-to-004.md   # Architectural Decision Records (ADRs 1–4)
│   │   └── ADR-005-platform-strategy.md # ADR 5: Dual-Client Architecture
│   └── testing/
│       ├── TESTING_STRATEGY.md # Test pyramid & comprehensive test cases
│       └── CRITICAL_FLOWS.md   # Critical flows & regression checklist
├── AGENTS.md                   # Core guidelines & domain rules for AI coding agents
└── README.md
```

---

## 🛠️ Tech Stack (Target Implementation)

### 1. Android Native App (`apps/mobile`)
- **Framework**: React Native + Expo (Managed Workflow)
- **Language**: TypeScript
- **Navigation**: Expo Router (file-based)
- **Styling**: NativeWind (Tailwind CSS for React Native)
- **Distribution**: Standalone APK via EAS Build (direct sharing to landlords)

### 2. Mobile Web (`apps/web`)
- **Framework**: React + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Primary Audience**: iPhone users accessing via Safari, and browser-based access

### 3. Backend API (`apps/api`)
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy 2.0 & Alembic migrations
- **Authentication**: JWT with bcrypt password hashing
- **Deployment**: Docker Compose behind Nginx

---

## 📜 Agent Guidelines

If you are an AI coding assistant or developer contributing to this repo, **read [`AGENTS.md`](./AGENTS.md) before writing any code.**
