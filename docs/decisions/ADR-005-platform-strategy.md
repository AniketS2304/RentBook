# ADR-005: Dual-Client Architecture — React Native Android APK & Mobile Web for iPhone

## Status

**Accepted**

## Context

The initial architectural assumption positioned RentBook as a single responsive React web application. However, real-world landlord behavior in India reveals:
1. Landlords are overwhelmingly mobile-first users who manage tenant communication and rent tracking directly from their smartphones.
2. The vast majority of target landlords in India use Android smartphones.
3. Requiring landlords to open a desktop browser or use mobile browser shortcuts for daily use introduces friction compared to a native application.
4. Submitting to the Google Play Store and Apple App Store during the initial MVP validation phase introduces unnecessary review delays, developer account costs, and compliance overhead.
5. iPhone users still require seamless access, but distributing test iOS apps outside the App Store (TestFlight/AdHoc) is cumbersome for non-technical users.

## Decision

Adopt a **dual-client mobile-first architecture** powered by a single shared FastAPI backend:

1. **Primary Client — Native Android App (`apps/mobile`)**:
   - Built with React Native, Expo (Managed Workflow), TypeScript, NativeWind, and Expo Router.
   - Built into a standalone APK (`RentBook.apk`) via Expo Application Services (EAS Build).
   - Distributed directly to early real-world landlords via WhatsApp, direct link, or USB install.
2. **Secondary Client — Mobile Web (`apps/web`)**:
   - Built with React, Vite, TypeScript, and Tailwind CSS.
   - Hosted statically on HTTPS and optimized specifically for mobile browsers (iPhone Safari and Android Chrome).
   - Serves iPhone users without requiring an App Store listing.
3. **Unified Backend (`apps/api`)**:
   - FastAPI + PostgreSQL serves identical JSON endpoints (`/api/v1/*`) to both clients.
   - Single source of truth for all business rules, statuses, and data integrity.

## Options Considered

### Option A: Web-Only Responsive SPA (Original Assumption)
- ❌ Inferior touch experience on Android; no native hardware back button or native keyboard handling.
- ❌ Landlords expect an "app" they can install on their Android home screen.

### Option B: Separate Native Apps (Kotlin for Android, Swift for iOS)
- ❌ Massive overhead; two separate native mobile codebases plus a backend.
- ❌ Prohibitive for an MVP.

### Option C: React Native (Expo) Android APK + React (Vite) Mobile Web (Chosen)
- ✅ Native performance, gestures, and direct APK distribution for Android landlords.
- ✅ Instant access for iPhone users via Safari over HTTPS.
- ✅ React Native codebase can compile to iOS native in Phase 2 via EAS Build if demand justifies.
- ✅ Shared backend ensures business rules are never duplicated.

## Consequences

**Positive**:
- Direct distribution of Android APK enables instant user onboarding without Play Store friction.
- Both Android and iPhone landlords are fully supported in MVP.
- Clean separation between clients and business logic.

**Trade-offs & Mitigations**:
- Maintaining two client presentation codebases (`apps/mobile` and `apps/web`).
- *Mitigation*: Both clients share the exact same REST API contracts and data models. No business logic (rent status calculation, generation rules, dashboard aggregation) is placed on either client; it resides solely in backend services.
