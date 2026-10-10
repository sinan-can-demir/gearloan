# Admin Guide

## Roles

| Role | Access |
|------|--------|
| Student | Browse items, request bookings, extend loans |
| Faculty | Same as student, with auto-approval for standard gear |
| Admin | All of the above, plus approve requests, manage inventory, import rosters, log conditions, set fees |

Set a user's role under **Admin → Accounts → Users → role field**.

## Managing inventory

Go to **Admin → Inventory → Items**.

- **loan_days** — how many days the borrower keeps the item by default.
- **high_value** — tick this to require admin approval for every request, regardless of role.
- **course** — link to a course to reserve this item for enrolled students (they get instant approval; others need admin approval).
- **replacement_cost** — used as the ceiling for damage charges.
- **is_available** — untick to hide the item from borrowers and block new requests.

## Approving booking requests

Go to **Admin → Bookings → Bookings** and filter by status = `requested`.
Open a booking and change its status to `approved`. The borrower receives an email.

Alternatively, use the list action **Approve selected bookings** (add this to your
`BookingAdmin` if desired).

## Check-out and check-in

Check-out and check-in are done via the service layer (`apps/bookings/services.py`).
Each creates a `ConditionLog` entry. You can view logs under **Admin → Bookings → Condition logs**.

## Fees

Late fees ($10/day) are calculated automatically when `apply_late_fee` is called.
Damage fees are added manually via **Admin → Fees → Fees → Add fee**.

To waive a fee, tick the **waived** checkbox in the fee record.

## Scheduled notifications

Run these two tasks daily (cron, Celery beat, or a management command):

```python
from apps.notifications.tasks import send_due_date_reminders, send_overdue_notices

send_due_date_reminders()   # emails borrowers with items due tomorrow
send_overdue_notices()      # marks overdue bookings and emails borrowers
```

## Importing rosters

See [roster-import.md](roster-import.md).
