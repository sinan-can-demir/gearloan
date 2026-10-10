# Patch notes 002: scoped additions

*Status: backlog — see V1_PLAN.md for what is in scope for v1.*

Builds on `PATCH_NOTES_001.md`. Where these notes conflict with the README or
patch notes 001, these notes win.

Features listed here but not in `V1_PLAN.md` are deferred:

- Waitlist
- Pickup and return logistics (locations and windows)
- Lost-item reporting flow (v1 can set a unit to `lost` by hand)
- Semester rollover tool
- QR codes and scanning
- Photos and ID checks at check-out
- Reports and CSV export
- Real multi-department interface
- Extra account types beyond student / faculty / admin
- Accessibility work beyond basic good practice

Features from these notes that **are** in v1:

- Fee status (unpaid / paid / waived / disputed) with `external_reference`
- Hold rule: overdue items block new bookings; `max_active_loans` per role
- Audit and event log (`AuditEvent`)
- Department scaffold (model + FK, no interface changes)
- Role table replacing the fixed three roles
- `Term` model; `Course` FK to `Term`
- Unit statuses: scheduled_maintenance, lost_pending, lost (admin sets by hand)
