# GearLoan

Open source equipment booking for college music departments. Track instruments and gear, let students and faculty borrow them, and give admins the rules and tools to keep it all running. Free to use, free to self-host.

> GearLoan is a working name. Rename it whenever you like.

## Features (planned)

- Two interfaces: borrower and admin
- Inventory of instruments and gear, with per-item loan lengths
- Items can be reserved for a course (for example, cellos for cello students)
- Auto-approval for gear tied to a student's class, admin approval for everything else
- Faculty requests auto-approve for standard gear, and go to an admin for high-value or reserved items
- Class roster import from CSV (Canvas and other connectors can come later)
- Extensions: rebook while you still hold the item, if nobody else has reserved it
- First come, first served
- Check-out and check-in condition logging for every loan
- Late fee of $10 per day, and damage charges up to replacement cost
- Email notifications and reminders

## Requirements

### Roles

| Role | Can do |
|------|--------|
| Student | Browse items, request bookings, extend loans |
| Faculty | Same as students, with auto-approval for standard gear |
| Admin | Approve requests, manage inventory, import rosters, log conditions, set fees |

### Booking rules

- Each item has its own default loan length (a week, a month, a semester). Admins set it.
- Students get instant approval for items reserved for a course they are enrolled in.
- Students need admin approval for all other items.
- Faculty get instant approval for standard gear. High-value and reserved items need admin approval.
- Faculty can optionally get longer limits on the same items.
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
| `User` | Email and role (student, faculty, admin) |
| `Course` | Name and term |
| `Enrollment` | Links users to courses (filled by CSV import) |
| `Item` | Name, loan length, high-value flag, optional reserved course |
| `Booking` | User, item, status, due date |
| `ConditionLog` | Check-out and check-in notes for a booking |
| `Fee` | Late fees and damage charges for a booking |

Booking statuses: requested, approved, checked out, returned, overdue, cancelled.

## Tech stack

- Python and Django (logins, admin interface, ORM, and email come built in)
- SQLite for local development, PostgreSQL for production
- Docker and docker-compose for one-command installs

## Quick start (Docker)

```bash
git clone https://github.com/YOUR-NAME/gearloan.git
cd gearloan
cp .env.example .env
docker compose up --build
```

Then open http://localhost:8000.

## Quick start (no Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Roster import

Admins upload a CSV file to link students to courses. Expected columns:

```
email,course_name,term
student@college.edu,Cello I,Fall 2026
```

Importing is built as a separate module so other roster sources (Canvas, Banner) can be added later without touching the core.

## Roadmap

1. Project skeleton, Docker setup, user roles
2. Inventory: items, course reservations
3. Booking requests and approval rules
4. Check-out and check-in with condition logs
5. Late fees, damage charges, extensions
6. Email notifications
7. CSV roster import
8. Documentation for departments installing it

## Contributing

Contributions are welcome. Open an issue to discuss an idea, or send a pull request. See `CONTRIBUTING.md` (to be written).

## License

MIT (suggested). Add a `LICENSE` file before publishing.
