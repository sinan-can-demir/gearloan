# GearLoan

Open source equipment booking for college music departments. Track instruments and gear, let students and faculty borrow them, and give admins the rules and tools to keep it all running. Free to use, free to self-host.

> GearLoan is a working name. Rename it whenever you like.

## Status

**v1.0.0 released 2026-10-10.** 76 tests pass. Docker image published to ghcr.io. See [V1_PLAN.md](V1_PLAN.md) for what is in scope and what is deferred.

**What works:** inventory management, booking requests and approval, check-out/check-in with condition logs, late fees, CSV roster import, email notifications, audit log.

**Deferred:** waitlist, kit bundles, QR/barcode lookup, photo uploads, reports, multi-department UI, rollover.

## Features

- Two interfaces: borrower and admin
- Two-level inventory: `ItemType` (rules, loan length, approval mode) and `Unit` (each physical copy with an asset tag)
- Auto-approval for gear tied to a student's enrolled course; admin approval for everything else
- Faculty requests auto-approve for standard gear; high-value and reserved items go to admin
- Role table controls per-role limits (max concurrent loans, approval permissions)
- Class roster import from CSV
- Extensions: rebook while you still hold the item, if nobody else has reserved it
- Check-out and check-in condition logging for every loan
- Late fee of $10 per day, and damage charges up to replacement cost
- Email notifications and reminders
- Audit log for all state changes

## Requirements

### Roles

Roles are stored in the `Role` table (not hardcoded). The seed command creates three defaults:

| Role | Can do | `max_active_loans` |
|------|--------|--------------------|
| Student | Browse items, request bookings, extend loans | 3 |
| Faculty | Same as students, with auto-approval for standard gear | Unlimited |
| Admin | Approve requests, manage inventory, import rosters, log conditions, set fees | Unlimited |

### Booking rules

- Each `ItemType` has its own default loan length. Admins set it.
- Students get instant approval for items reserved for a course they are enrolled in.
- Students need admin approval for all other items.
- Faculty get instant approval for standard gear. High-value and reserved items need admin approval.
- Hold rule: overdue loans block new requests. A per-role `max_active_loans` cap also applies.
- Requests are served first come, first served.

### Returns and fees

- Condition is logged at check-out and again at check-in, for everyone.
- Late return: $10 per day overdue.
- Damage: charged by severity, up to full replacement cost.

### Notifications

- Email for request status, due-date reminders, and overdue notices.

## Data model

| Table | Purpose |
|-------|---------|
| `Role` | Named role with permission flags and loan limits |
| `User` | Email and FK to `Role` (custom auth model) |
| `Department` | Department record; multi-department filtering is a v2 feature |
| `Term` | Academic term (name + dates) |
| `Course` | Name, term, and optional reserved-item link |
| `Enrollment` | Links users to courses (filled by CSV import) |
| `ItemType` | Gear category: loan length, approval mode, high-value flag |
| `Unit` | Physical copy of an `ItemType`; holds the asset tag (`CEL-003` style) |
| `Booking` | User, unit, status, due date, extension count |
| `ConditionLog` | Check-out and check-in notes for a booking |
| `Fee` | Late fees and damage charges for a booking |
| `AuditEvent` | Append-only log of all state changes (actor, action, details) |

Booking statuses: requested, approved, checked_out, returned, overdue, cancelled.

## Tech stack

- Python and Django (logins, admin interface, ORM, and email come built in)
- SQLite for local development, PostgreSQL for production
- Docker and docker-compose for one-command installs
- GitHub Actions CI on every push and release pipeline on every `v*.*.*` tag
- Docker image published to `ghcr.io/sinan-can-demir/gearloan`

## Quick start (Docker)

Pull the published image (no build required):

```bash
docker pull ghcr.io/sinan-can-demir/gearloan:latest
```

Or build from source:

```bash
git clone https://github.com/sinan-can-demir/gearloan.git
cd gearloan
cp .env.example .env
# Set SECRET_KEY in .env before starting
docker compose up --build
```

Then open http://localhost:8000. The first admin account must be created with:

```bash
docker compose exec web python manage.py createsuperuser
```

No default admin account is created automatically.

## Quick start (no Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set SECRET_KEY and DEBUG=True in .env
python manage.py migrate
python manage.py seed_roles       # creates the default Role rows
python manage.py createsuperuser
python manage.py runserver
```

## Roster import

Admins upload a CSV file to link students to courses. Expected columns:

```
email,course_name,term
student@college.edu,Cello I,Fall 2026
```

Importing is a separate module so other roster sources (Canvas, Banner) can be added later without touching the core.

## Roadmap

The v1 scope is tracked in [V1_PLAN.md](V1_PLAN.md). Deferred features are listed in [PATCH_NOTES_002.md](PATCH_NOTES_002.md).

Patch notes: [001](PATCH_NOTES_001.md) · [002](PATCH_NOTES_002.md) · [003](PATCH_NOTES_003.md)

Security: [THREAT_MODEL.md](THREAT_MODEL.md) · [SECURITY.md](SECURITY.md)

## Contributing

Contributions are welcome. Open an issue to discuss an idea, or send a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
