# Version 1 plan

*This file records the v1 scope decisions. It wins over the README and patch notes.*

## Goal

The smallest version a real music department could use: items and units,
a borrower interface, an admin interface, bookings with auto-approval rules,
check-out and check-in with condition logs, late fees, and email.

## Decisions

### Hold rule
- Overdue items block new bookings (enforced in `bookings/rules.py`).
- Each role has `max_active_loans` (null = unlimited).
- Pieces of the same booking group are exempt (future kit support).
- Admins can override; overrides are written to the audit log.

### Roles
- `User.role` is a FK to `Role` rather than a CharField.
- Seeded by `python manage.py seed_roles`: student, faculty, admin.
- Role fields: `name`, `can_borrow`, `auto_approve_level`, `can_check_in_out`,
  `can_approve`, `can_manage_inventory`, `max_active_loans`.

### Multi-department
- `Department` model exists; nullable FK on `ItemType`, `Unit`, `Course`, `Term`.
- `scoped_qs()` in `departments/helpers.py` is the single query entry point.
- No interface changes in v1.

## In scope for v1

- Role table and default roles
- Default department
- ItemType and Unit with asset tags
- Per-item rules: loan_days, replacement_cost, high_value, reserved_course,
  allowed_borrowers, approval_mode, max_extensions
- Courses, Terms, Enrollments, CSV roster import
- Borrower interface: browse, request, view loans, extend
- Admin interface: approve/reject, inventory, check-out, check-in
- Approval rules (all role × item-type combinations)
- Hold rule (overdue blocks; max_active_loans per role)
- Check-out and check-in with mandatory condition logs
- Late fees ($10/day, per-type override) and damage charges (capped)
- Fee status (unpaid / paid / waived / disputed) — record only
- Email: request status, due-date reminders, overdue notices, rejection
- Audit log for key events
- Docker, README, tests

## Deferred

Waitlist, kits, maintenance records, lost-item flow, semester rollover tool,
pickup locations, QR codes, photos, ID verification, reports, CSV export,
real multi-department behavior, extra roles, accessibility, translations.

## Commit order (completed)

1. Roles refactor
2. Department model and FK
3. Inventory (ItemType, Unit, tags, importer)
4. Courses and roster (Term, updated importer)
5. Bookings and rules (hold, booking_group, reject)
6. Check-out/check-in admin screens
7. Fees (status, lost type, change_fee_status)
8. Email (rejection and fee-status emails)
9. Audit log (AuditEvent, logger, read-only admin)
10. Polish (Dockerfile entrypoint, PATCH_NOTES, V1_PLAN)

## Acceptance checks

All covered by tests:
- Enrolled student + reserved cello → instant approval
- Same student + PA system → admin review
- Faculty + standard gear → instant approval
- Faculty + high-value gear → admin review
- Overdue item blocks new request
- Active loan does not block when max_active_loans is unlimited
- 3-day late loan → $30 (or per-type override)
- Damage charge never exceeds replacement cost
- Extension refused when another booking is pending
- Check-out and check-in each require a condition note
- Waiving a fee without a reason raises an error
