# ADR-006: MVP Authorization Strategy — JWT Authentication and Owner-Scoped Isolation

## Status

**Accepted**

## Context

RentBook is a digital rent register designed for individual landlords managing their properties, units, and tenants.

In the MVP phase:
1. The application serves exactly one authenticated user archetype: the **Owner / Landlord**.
2. Tenants are rental occupants and communication contacts, **not** authenticated application users.
3. Introducing Role-Based Access Control (RBAC), multi-tenant enterprise permissions, policy engines, or role assignment tables at this stage would introduce unnecessary schema complexity, runtime overhead, and development friction without providing value to real-world solo landlords.
4. At the same time, owner isolation is a critical security boundary: Owner A must never see, modify, or infer the existence of Owner B's properties, units, tenants, rent records, or payments.
5. The authorization architecture must be simple, rock-solid, and secure for MVP, while providing a clean evolution path to future multi-role support (e.g., property managers, assistants) without requiring an architectural rewrite.

## Decision

Adopt a **strict JWT authentication + owner-scoped authorization** model for MVP:

1. **No RBAC or Roles in MVP**:
   - The database contains no `roles`, `permissions`, or `user_roles` tables.
   - The `owners` table contains no `role` column.
   - There are no policy engines, permission matrices, or role-check middleware.

2. **Owner Identity from Authenticated JWT**:
   - Authentication is performed via standard JWT Bearer tokens issued upon owner login or registration.
   - The authenticated owner's identifier (`owner_id`) is extracted exclusively from the validated JWT payload by FastAPI dependency injection (`get_current_owner`).
   - The API will **never** accept `owner_id` from client-controlled inputs (request bodies, query parameters, path variables, or headers).

3. **Owner-Scoped Authorization & Full CRUD**:
   - Every authenticated owner has full CRUD (Create, Read, Update, Soft-Delete/Void) authority over all data entities belonging to them.
   - Authorization is implicit based on resource ownership: if a resource belongs to `owner_id`, the owner is authorized to operate on it.

4. **Mandatory Owner Isolation at the Repository Layer**:
   - Every repository and database query for user-owned resources must explicitly accept and filter by `owner_id`.
   - The ownership chain traces all resources back to `owner_id`:
     ```text
     Owner (owner_id from JWT)
      └── Property (owner_id)
           └── Unit (property.owner_id)
                └── Tenant (unit.property.owner_id)
                     └── Rent Record (tenant.unit.property.owner_id)
                          └── Payment (rent_record.tenant.unit.property.owner_id)
     ```
   - Direct-access queries must join or filter against `owner_id` to guarantee isolation at the data access level.

5. **Cross-Owner Access Returns 404 (Not 403)**:
   - If an authenticated owner requests an ID (property, unit, tenant, rent record, payment) that does not exist OR belongs to another owner, the API returns `HTTP 404 Not Found`.
   - Returning `403 Forbidden` leaks resource existence to malicious or unauthorized actors. Returning `404` maintains complete privacy and existence isolation.

6. **Future Multi-Role / RBAC Evolution Path**:
   - Staff, co-owners, and property manager roles remain deferred to future phases (Phase 2+).
   - When role-based access is introduced in the future, it will be modeled as a delegation layer on top of owner isolation (e.g., an `owner_memberships` or `property_access` junction table with granular permissions like `can_record_payment`, `can_edit_rent`).
   - The fundamental security boundary will remain property/owner ownership; roles will merely scope what a delegated actor can do within an owner's existing domain. This ensures zero breaking rewrites to existing core business logic or repository queries.

## Options Considered

### Option A: Full RBAC / Policy Engine (Roles, Permissions, Role Mappings)
- ❌ Massive overengineering for an MVP with only one user type (Landlords).
- ❌ Complex database migrations, extra query joins, and testing overhead.
- ❌ High cognitive load and violation of the core project principle: "Keep it simple. This is a digital register, not enterprise software."

### Option B: Simple Role Column on Owners Table (`role: 'OWNER' | 'ADMIN'`)
- ❌ Dead code / false abstraction: every authenticated user is an owner, so checking `role == 'OWNER'` provides zero security value.
- ❌ Encourages premature abstractions before multi-user delegation requirements are understood.

### Option C: JWT Authentication + Owner-Scoped Authorization (Chosen)
- ✅ Minimal, elegant, and perfectly aligned with MVP scope.
- ✅ Zero unnecessary database columns or tables.
- ✅ Maximum security: strict `owner_id` filtering on all queries and 404 on mismatched ownership prevents data leakage.
- ✅ Clear, non-breaking upgrade path to future delegated roles.

## Consequences

**Positive**:
- Eliminates complex authorization boilerplate from the MVP codebase.
- Enforces strict data isolation at the repository query boundary.
- Prevents existence enumeration through uniform 404 responses.
- Keeps backend routes, schemas, and models lean and focused.

**Trade-offs & Mitigations**:
- Multi-user management (e.g., landlord inviting a helper or property manager) is not supported in MVP.
- *Mitigation*: This is an explicit, deliberate non-requirement for MVP (documented in `MVP_SCOPE.md` and `ROADMAP.md`). Landlords managing their own registers do not need delegated accounts in initial validation. When needed in Phase 2, delegation tables can be layered onto the existing owner-scoped architecture without altering the core ownership model.
