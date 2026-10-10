# Patch notes 001: item rules, asset tags, and unit tracking

*Status: implemented in main.*

These notes changed the requirements and data model from the first design pass.
Where they conflict with `README.md`, these notes win.

## 1. Items split into two levels

The single `Item` table was replaced by two tables.

| Table | Holds |
|-------|-------|
| `ItemType` | The rules for a kind of gear (for example "Cello, 4/4") |
| `Unit` | One physical copy with its own asset tag, status, and history |

## 2. Asset tags

- Every `Unit` has a unique `asset_tag` such as `CEL-003` or `MIC-014`.
- `apps/inventory/tags.py` generates the next tag from the type's prefix.

## 3. Per-item rules (on `ItemType`)

| Field | Purpose |
|-------|---------|
| `name` | e.g. "Cello, 4/4" |
| `tag_prefix` | generates asset tags (`CEL`) |
| `loan_days` | default loan length |
| `replacement_cost` | cap for damage charges |
| `high_value` | requires admin approval for faculty |
| `reserved_course` | optional; reserved for students in this course |
| `allowed_borrowers` | students, faculty, or both |
| `approval_mode` | always auto, always admin, or auto only for the reserved course |
| `max_extensions` | none, one, or unlimited |
| `late_fee_per_day` | optional override of the global $10/day |
| `category` | for category defaults (see patch notes 002) |

## 4. Unit fields

| Field | Purpose |
|-------|---------|
| `asset_tag` | unique human-readable ID |
| `item_type` | FK to rules |
| `status` | available, checked_out, in_repair, scheduled_maintenance, lost_pending, lost, retired |
| `notes` | serial number, purchase date, etc. |

## 5. Blackout dates

Deferred to a later version.

## 6. Inventory CSV import

`apps/inventory/importers/csv_importer.py` — columns:
`type_name, tag_prefix, loan_days, replacement_cost, high_value, reserved_course_name, reserved_course_term, quantity`

## 7. Data model changes

- `Booking.item_id` → `Booking.unit_id`
- `ConditionLog` tied to the booking and through it to the unit
- `Fee` caps damage charges at `ItemType.replacement_cost`
- Auto-approval logic reads `approval_mode`, `allowed_borrowers`, `high_value`
