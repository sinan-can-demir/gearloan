# Roster Import

GearLoan can link students to courses by importing a CSV file. This is the first
step to enabling auto-approval for course-reserved instruments.

## CSV format

The file must have a header row with at least these three columns (order does not matter):

```
email,course_name,term
student@college.edu,Cello I,Fall 2026
another@college.edu,Cello I,Fall 2026
```

- **email** — must match an existing GearLoan user account.
- **course_name** — the course will be created if it does not already exist.
- **term** — free text, e.g. `Fall 2026`, `Spring 2027`.

Extra columns are ignored.

## Importing from the Django admin

1. Log in as an admin and go to `/admin/`.
2. Under **Courses**, open **Import roster** (or upload via the management command below).
3. Upload your CSV file and submit.
4. A summary shows how many enrollments were created, skipped, or failed.

## Importing from the command line

```bash
python manage.py import_roster path/to/roster.csv
```

## What happens during import

- For each row, GearLoan looks up the user by email.
- If the course + term combination does not exist it is created.
- If the enrollment already exists it is skipped (no duplicates).
- Rows with unknown email addresses are logged as errors; the rest continue.

## Adding other roster sources

The importer is built around the `RosterImporter` abstract class in
`apps/courses/importers/base.py`. To add a Canvas or Banner connector:

1. Create a new file in `apps/courses/importers/`.
2. Subclass `RosterImporter` and implement `import_roster(source)`.
3. Return an `ImportResult`.

No changes to the core booking logic are needed.
