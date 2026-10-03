# Client Architecture & API Integration — RentBook

This document specifies the client architecture and API integration foundation for both RentBook client applications:
1. **Android Native App** (`apps/mobile`): React Native + Expo + TypeScript (direct standalone APK via EAS)
2. **Mobile Web App** (`apps/web`): React + Vite + TypeScript (mobile-first responsive web for iPhone Safari and mobile browsers)

Both clients communicate with the **FastAPI + PostgreSQL** backend API (`apps/api`).

---

## 1. Directory Structure

### Mobile Client (`apps/mobile/`)

```text
apps/mobile/
├── assets/                 # App icons, splash screens, assets
├── src/
│   ├── api/
│   │   ├── __tests__/      # ApiClient and token storage unit tests
│   │   ├── client.ts       # Centralized ApiClient with refresh mutex queue
│   │   ├── endpoints.ts    # Strongly typed API endpoints for all backend resources
│   │   ├── errors.ts       # Normalized ApiClientError and parseApiError
│   │   └── index.ts        # Public API exports
│   ├── auth/
│   │   ├── AuthContext.tsx # Authentication provider and useAuth hook
│   │   └── tokenStorage.ts # expo-secure-store adapter with in-memory fallback
│   ├── config/
│   │   └── env.ts          # Configurable API base URL (10.0.2.2:8000 for Android emulator)
│   ├── screens/
│   │   ├── DashboardScreen.tsx     # Overview cards & metrics
│   │   ├── LoginScreen.tsx         # Landlord login
│   │   ├── PlaceholderScreens.tsx  # Properties, Tenants, Rent, Payments, Reminders, Reports, Settings
│   │   └── RegisterScreen.tsx      # New owner registration
│   ├── types/
│   │   └── api.ts          # Exact TypeScript interfaces matching FastAPI schemas
│   └── utils/
│       └── format.ts       # Paise to ₹ currency and ISO date formatting
├── App.tsx                 # Root component with AuthProvider and tab navigation
├── app.json                # Expo configuration with Android package & plugins
├── eas.json                # Standalone APK build profiles for EAS
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
└── vitest.config.ts        # Unit test configuration
```

### Web Client (`apps/web/`)

```text
apps/web/
├── public/                 # Static public assets
├── src/
│   ├── api/
│   │   ├── __tests__/      # ApiClient and refresh mutex unit tests
│   │   ├── client.ts       # Centralized ApiClient with refresh mutex queue
│   │   ├── endpoints.ts    # Strongly typed API endpoints for all backend resources
│   │   ├── errors.ts       # Normalized ApiClientError and parseApiError
│   │   └── index.ts        # Public API exports
│   ├── auth/
│   │   ├── AuthContext.tsx # Authentication provider and useAuth hook
│   │   └── tokenStorage.ts # In-memory access token + tab session refresh storage
│   ├── config/
│   │   └── env.ts          # Vite env config (import.meta.env.VITE_API_URL)
│   ├── pages/
│   │   ├── Dashboard.tsx   # Dashboard cards & metrics
│   │   ├── Login.tsx       # Landlord login
│   │   ├── Placeholders.tsx# Properties, Tenants, Rent, Payments, Reminders, Reports, Settings
│   │   └── Register.tsx    # Owner registration
│   ├── types/
│   │   └── api.ts          # Exact TypeScript interfaces matching FastAPI schemas
│   ├── utils/
│   │   └── format.ts       # Paise to ₹ currency and ISO date formatting
│   ├── App.tsx             # Root component with AuthProvider and mobile shell
│   └── main.tsx            # Application entrypoint
├── .env.example            # Environment template
├── index.html              # HTML entrypoint
├── package.json            # Dependencies and scripts
├── tsconfig.app.json       # App TypeScript configuration
├── tsconfig.json           # Project references
├── vite.config.ts          # Vite configuration
└── vitest.config.ts        # Vitest test configuration
```

---

## 2. Shared Domain & Typing Rules

To prevent client-server drift and preserve single-source-of-truth principles:

1. **Monetary Values**:
   - Always represented as integer numbers in paise (`amount_paise: number`).
   - Formatting into ₹ (e.g. `₹8,000`) is done exclusively at the display layer using `formatPaiseToRupees()`.
2. **Dates & Timestamps**:
   - Calendar dates are ISO 8601 strings: `YYYY-MM-DD`.
   - Timestamps are ISO 8601 UTC strings: `YYYY-MM-DDTHH:MM:SSZ`.
3. **Identifiers**:
   - All IDs are standard UUID strings.
4. **Backend Enums**:
   - `RentStatus`: `"PENDING" | "DUE" | "OVERDUE" | "PAID" | "PARTIALLY_PAID"`
   - `PaymentMethod`: `"CASH" | "UPI" | "BANK_TRANSFER" | "OTHER"`
   - `TenantStatus`: `"ACTIVE" | "INACTIVE"`
   - `UnitType`: `"FLAT" | "ROOM" | "SHOP" | "OTHER"`

---

## 3. Centralized API Client Architecture

Both clients use identical centralized API clients rather than scattering raw `fetch` calls.

```text
UI Component
     │
     ▼
API Service Function (e.g. api.dashboard.getSummary())
     │
     ▼
Centralized ApiClient (client.ts)
  ├─ Injects `Authorization: Bearer <access_token>`
  ├─ Manages request timeout (AbortController)
  ├─ Catches 401 & triggers Refresh Mutex Queue
  └─ Normalizes all responses & errors (ApiClientError)
     │
     ▼
FastAPI Backend (/api/v1/*)
```

### Key Capabilities

1. **Single Base URL**:
   - Configured via environment (`VITE_API_URL` for web, `EXPO_PUBLIC_API_URL` for mobile).
2. **Timeout Handling**:
   - Configurable timeout (default 15,000 ms).
   - Aborts hanging requests via standard `AbortController`.
   - Throws `ApiClientError` with `isTimeout: true`.
3. **Normalized Error Model (`ApiClientError`)**:
   - Exposes `status`, `message`, `code`, `errors` (field errors), `isNetworkError`, `isTimeout`.
   - Helper getters: `isUnauthorized`, `isForbidden`, `isNotFound`, `isValidationError`, `isConflict`, `isServerError`.
   - Protects users from internal stack traces or database errors.

---

## 4. Token Storage & Refresh Strategy

### Access vs Refresh Tokens
- **Access Token**: Short-lived (30 minutes). Kept **in-memory** in both clients for security.
- **Refresh Token**: Long-lived (7 days). Rotated on every refresh call.

### Storage per Platform
- **Android Native App**:
  - Secure storage via `expo-secure-store` (hardware-backed Android Keystore / encrypted SharedPreferences).
  - Test/Node fallback to in-memory storage for clean unit testing without native crashes.
- **Mobile Web App**:
  - Access token kept strictly in memory.
  - Refresh token kept in tab session storage (`sessionStorage`) to survive page reloads within the tab session.

### Refresh Mutex Queue (Preventing Refresh Storms)

When an access token expires:
1. The first request receiving a `401 Unauthorized` sets `isRefreshing = true` and initiates a single `POST /api/v1/auth/refresh`.
2. Any concurrent requests that also encounter a 401 are held in a waiting queue (`refreshSubscribers`).
3. When the refresh request succeeds:
   - The new `access_token` and rotated `refresh_token` are saved to storage.
   - All queued requests are resolved and retried with the new access token.
4. When the refresh request fails:
   - All tokens are cleared.
   - All queued requests are rejected.
   - The `onAuthFailure` callback triggers `logout()`, routing the user to the Login screen.
5. Loop prevention: requests marked `_retry: true` or calls to `/auth/*` will never trigger a recursive refresh loop.

---

## 5. Development & Environment Configuration

### Web Client
- Development server: `npm run dev` in `apps/web` (defaults to `http://localhost:5173`)
- Connected backend: `http://localhost:8000/api/v1`
- Production build: `npm run build`

### Mobile Client
- Expo start: `npm start` in `apps/mobile`
- **Android Emulator**:
  - Inside the Android emulator, `localhost` refers to the emulator itself.
  - The mobile client automatically defaults to `http://10.0.2.2:8000/api/v1` on Android.
- **Physical Android Device (via Wi-Fi)**:
  - Set `EXPO_PUBLIC_API_URL=http://<YOUR_COMPUTER_LAN_IP>:8000/api/v1` in `apps/mobile/.env`.
- **Physical Android Device (via USB ADB Reverse)**:
  - Run `adb reverse tcp:8000 tcp:8000`
  - Set `EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1`.
- **Standalone Android APK**:
  - Configured in `eas.json` under the `preview` and `production` profiles with `"buildType": "apk"`.
  - Build command: `eas build -p android --profile preview`.

---

## 6. Documented API / Contract Observations

During client integration, the following observations were verified against the frozen backend:

1. **Refresh Response Token Rotation**:
   - `docs/architecture/API.md` line 109 shows `/api/v1/auth/refresh` returning only `{ access_token, token_type }`.
   - The backend service (`app.services.auth.AuthService`) actually rotates the refresh token and returns `{ access_token, refresh_token, token_type }`.
   - Both clients' `ApiClient` are designed to handle both scenarios, saving the rotated `refresh_token` when provided.
2. **Web Refresh Token Cookie Strategy**:
   - The current backend API returns `refresh_token` in the JSON response body rather than an `HttpOnly` cookie.
   - Per Phase 10 rules, the backend was left unchanged (frozen). The web client securely stores the access token in memory and uses a pluggable session storage adapter for the refresh token.
