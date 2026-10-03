# ADR-007: Web Refresh-Token Storage & Cookie Migration Strategy

## Status

- **CURRENT**: In-Memory Access Token + Scoped `sessionStorage` Refresh Token (Phase 10 Baseline)
- **TARGET**: In-Memory Access Token + `HttpOnly` Secure `SameSite` Cookie Refresh Token (Targeted for Web Production Hardening)

---

## Context

In Phase 10, the client architecture foundation was established for both the Android native client (`apps/mobile`) and the mobile web client (`apps/web`).

The security constraints established for the token lifecycle are:
- **Access Token**: Short-lived (30 minutes). Kept strictly **in memory** across both clients. Never persisted to disk or plain persistent storage.
- **Refresh Token**: Long-lived (7 days). Rotated on every single refresh call.
- **Android Platform (`apps/mobile`)**: Uses `expo-secure-store`, backed by hardware-backed Android Keystore and encrypted preferences. This fulfills platform security standards for mobile native apps.
- **Web Platform (`apps/web`)**: The existing frozen FastAPI API contract (`apps/api`) returns `access_token` and `refresh_token` in the JSON response payload. It does not set `Set-Cookie` headers. Consequently, the web client temporarily stores the refresh token in `sessionStorage` (scoped to the active tab session).

This ADR evaluates the security trade-offs of the current web implementation and designs the exact target architecture required to migrate the web client to `HttpOnly` cookies prior to production deployment without disrupting the frozen backend or breaking the Android client.

---

## 1. Security Analysis of Current Architecture

### Current Web Model
```text
Browser Tab (apps/web)
├── Memory: Access Token (30 min)
└── sessionStorage: Refresh Token (7 days)
```

### Security Trade-Offs

| Threat Vector | In-Memory Access Token | `sessionStorage` Refresh Token | `HttpOnly` Cookie Refresh Token (Target) |
|---------------|------------------------|--------------------------------|------------------------------------------|
| **XSS Token Exfiltration** | Mitigated (lost on refresh/tab close, inaccessible from other origins) | ⚠️ **Vulnerable**: Any injected script can call `sessionStorage.getItem()` and exfiltrate the token | ✅ **Immune**: Inaccessible to JavaScript runtime via `document.cookie` |
| **CSRF** | ✅ Immune (Bearer token in `Authorization` header cannot be auto-attached by browsers) | ✅ Immune (Requires JavaScript to attach payload) | ⚠️ Requires `SameSite=Lax/Strict` + scoped path protection |
| **Tab Isolation** | Isolated to tab | Scoped to individual tab (cleared when tab closes; not shared across tabs/windows) | Shared across all tabs of same origin |
| **Token Replay / Hijacking** | Limited to 30 min window | ⚠️ If exfiltrated before expiration, attacker can rotate and steal session | Inaccessible to scripts; rotation invalidates stolen tokens upon reuse |

### Key Takeaway
While keeping the short-lived access token in memory provides strong protection against silent long-term persistence attacks, holding the long-lived refresh token in JavaScript-accessible storage (`sessionStorage`) leaves the web client exposed to token theft in the event of any Cross-Site Scripting (XSS) vulnerability.

---

## 2. Target Architecture

### Decision
Migrate the web client authentication flow to **dual-mode token handling**:
1. **Access Token**: Stored strictly **in memory** in the web client, attached via `Authorization: Bearer <token>`.
2. **Refresh Token**: Transferred via an **`HttpOnly` + `Secure` + `SameSite=Lax` Cookie**, scoped strictly to the `/api/v1/auth` path.
3. **Android Native Client**: Retains its existing, highly secure JSON payload + `expo-secure-store` mechanism without any breaking changes.

---

## 3. Required Changes for Target Migration

### A. Backend API Changes (`apps/api`)

1. **Dual-Mode Response in `/auth/login` and `/auth/register`**:
   - For web requests (detected via Origin or standard `Set-Cookie` behavior), set cookie:
     ```http
     Set-Cookie: refresh_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=604800
     ```
   - Continue returning `access_token` and `token_type` in JSON response.
   - For mobile native clients, continue returning `refresh_token` in JSON payload (or accept a query/header flag `?mode=native` / client identification).

2. **Dual-Mode `/auth/refresh`**:
   - Inspect request:
     - If `refresh_token` is present in HTTP cookies: use cookie value.
     - Else if `refresh_token` is present in JSON request body: use body value.
   - On successful rotation:
     - Issue new 30-min `access_token` in JSON body.
     - Issue new rotated `refresh_token` via updated `Set-Cookie` header (and JSON body for mobile).

3. **Explicit `/auth/logout`**:
   - Provide a dedicated logout endpoint to revoke the active session and expire the cookie:
     ```http
     Set-Cookie: refresh_token=; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=0
     ```

4. **CORS Configuration**:
   - FastAPI `CORSMiddleware` must specify explicit web origins (e.g. `http://localhost:5173`, `https://app.rentbook.in`).
   - Must set `allow_credentials=True`. Wildcard (`allow_origins=["*"]`) cannot be used when cookies are transmitted.

### B. Web Client Changes (`apps/web`)

1. **HTTP Requests**:
   - Add `credentials: 'include'` to `fetch()` calls in `ApiClient` for auth endpoints (`/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/logout`).
2. **Storage Adapter**:
   - Deprecate `WebTabTokenStorage` in favor of a `CookieHttpOnlyTokenStorage`.
   - Client JavaScript no longer reads or writes the refresh token. The browser handles refresh-token storage and transmission automatically.
3. **Refresh Invocation**:
   - On 401, `ApiClient` calls `POST /auth/refresh` with an empty JSON body and `credentials: 'include'`. The browser automatically includes the `HttpOnly` cookie.

---

## 4. CSRF, SameSite & Local Development Considerations

### CSRF Protection
- All data-mutating endpoints (`/properties`, `/tenants`, `/rent`, `/payments`, etc.) require `Authorization: Bearer <access_token>`. Because browsers do NOT automatically attach `Authorization` headers on cross-site requests, these endpoints remain **100% immune to CSRF**.
- The only endpoint receiving the cookie is `/api/v1/auth/refresh` (scoped by `Path=/api/v1/auth`). Setting `SameSite=Lax` ensures cross-site POST requests from external sites will not attach the cookie.

### Local Development Handling
- **Cross-Port Origins**: In development, Vite runs on `http://localhost:5173` while FastAPI runs on `http://localhost:8000`.
- Modern browsers (Chrome, Firefox, Safari) treat `localhost` as a secure origin, allowing `SameSite=Lax` cookies with `credentials: 'include'` when CORS `allow_credentials=True` is properly configured.
- For production, both client and API can be hosted under the same domain (e.g., `app.rentbook.in` and `api.rentbook.in` or via reverse proxy `/api/*`), eliminating cross-origin cookie restrictions entirely.

---

## 5. Migration Verdict & Timing

### Should migration happen before production deployment?
**YES.**
- The current Phase 10 implementation (`sessionStorage` for web, `expo-secure-store` for mobile) is fully functional, cleanly tested, and adheres to the **backend freeze** constraint of Phase 10.
- However, prior to **public production deployment of the web client**, migrating the web refresh token to `HttpOnly` cookies is strongly recommended to eliminate the XSS token exfiltration attack surface.
- The migration should be scheduled as a dedicated backend + web security hardening task (Phase 11 or Pre-Production Deployment Gate) without destabilizing core business logic.
