# Platform Strategy — RentBook

## Product Vision & Platform Split

RentBook is a **mobile-first digital rent register** designed for Indian landlords managing residential and commercial properties. Because the majority of target landlords in India run their daily communication and property tracking entirely from smartphones, RentBook prioritizes the mobile experience above all else.

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
                       Direct APK         iPhone Safari /
                      Distribution        Mobile Browser
```

---

## 1. MVP Strategy

### Primary Platform: Android Native App

- **Framework**: React Native with Expo (Managed Workflow), TypeScript
- **Routing**: Expo Router (file-based navigation)
- **Styling**: NativeWind (Tailwind CSS for React Native)
- **Target OS**: Android 8.0+ (API Level 26+)
- **Distribution Method**: **Direct APK Distribution via EAS Build**
  - No Google Play Store listing required for initial MVP validation
  - Fast turnaround: Developers generate `RentBook.apk` via Expo Application Services (EAS Build)
  - Direct sharing via WhatsApp, direct download link, or USB install directly to early landlord users
  - Eliminates Play Store review delays, developer account barriers, and compliance overhead during MVP phase

### Secondary Platform: Mobile Web (iPhone / Browser)

- **Framework**: React, Vite, TypeScript
- **Styling**: Tailwind CSS
- **Primary Target Audience**: iPhone users accessing via Safari, as well as Android users preferring browser access or tablet/desktop check-ins
- **Distribution Method**: Hosted static web application served over HTTPS
- **UX Goal**: Replicate the exact mobile app look, feel, and workflows inside Safari/Chrome without requiring an App Store installation

---

## 2. Shared Backend: Single Source of Truth

Both clients consume the identical FastAPI REST API:

```text
React Native Android (apps/mobile) ──┐
                                     ├── FastAPI (apps/api) ─── PostgreSQL
React Mobile Web (apps/web) ─────────┘
```

### Strict Client-Backend Boundary
1. **Zero Duplicated Business Logic**: All rent status computations, generation boundaries, due date checks, and collection totals are calculated exclusively by backend services. Clients strictly render received states and capture user input.
2. **Unified API Contract**: Both clients call `/api/v1/*`. There are no platform-specific endpoints (`/android/*` or `/web/*`).
3. **Identical Workflows**: The steps to record a payment, view overdue tenants, or trigger a WhatsApp reminder are identical across Android and Web.

---

## 3. Platform Capabilities & UX Matrix

| Feature / Capability | Android Native App (`apps/mobile`) | Mobile Web (`apps/web`) |
|----------------------|-----------------------------------|-------------------------|
| **Primary User Base** | Android phone users (Landlords) | iPhone Safari users |
| **Technology** | React Native + Expo | React + Vite |
| **Distribution** | Standalone APK (EAS Build) | HTTPS URL (Nginx / Static Host) |
| **Navigation** | Expo Router (Native Tabs & Stacks) | React Router (Mobile Shell) |
| **Back Button** | Hardware/gesture back supported | Browser back button |
| **Keyboard** | Native keyboard avoiding view | Mobile browser virtual keyboard |
| **WhatsApp Reminders** | Native deep link (`Linking.openURL`) | Web deep link (`window.open` / `wa.me`) |
| **Token Storage** | Expo SecureStore | Browser `localStorage` / Cookie |
| **Offline Awareness** | NetInfo network status indicators | Browser online/offline events |
| **Viewport Handling** | Native screen bounds | Safe area insets (`env(safe-area-inset-*)`), `100dvh` |

---

## 4. Phase 2 & Future Platform Evolution

> [!NOTE]
> Future platform additions must not influence or complicate MVP architecture.

- **iOS Native App**: Because `apps/mobile` is built using React Native and Expo, an iOS native build can be compiled via EAS Build in Phase 2 once demand is validated, requiring zero backend changes and minimal UI adjustments.
- **App Store & Play Store Listings**: Transition from direct APK to Google Play Store and Apple App Store in Phase 2/3.
- **Push Notifications**: Expo Notifications for automated payment reminders and due-date alerts.
