# Patch notes 003: make a fresh install actually work

Source: a review of the repository at commit `f2e0906` (28 commits, 66 passing tests). Builds on `V1_PLAN.md` and patch notes 001 and 002. Where these notes conflict with earlier files, these notes win.

## Why this patch exists

A fresh install does not create the app's database tables. The tests pass anyway, which hid the problem. Fix this before any new feature work.

## 1. Blocking: commit database migrations

**Problem.** No migration files are tracked for the project's apps. Running `python manage.py migrate` on an empty database creates only Django's built-in tables. The Dockerfile and docker-compose both run `migrate`, so a Docker install starts a server with no tables for users, items, bookings, or fees. Tests pass because Django's test runner builds tables straight from the models for apps without migrations.

**Fix.**

1. Create a `migrations/` package (with `__init__.py`) in each app: `accounts`, `departments`, `courses`, `inventory`, `bookings`, `fees`, `audit`.
2. Generate the initial migrations: `python manage.py makemigrations accounts departments courses inventory bookings fees audit`.
3. Check that `AUTH_USER_MODEL` is migrated before anything that references it, and that the app dependency order resolves cleanly.
4. Commit the generated files. Do not add `migrations/` to `.gitignore`.
5. Make sure the role seed (`seed_roles`) and the default department are created by a data migration or by the startup command, and that running either twice does no harm.

**Acceptance checks.**

- On an empty SQLite database, `migrate` creates every model's table.
- On an empty PostgreSQL database (docker compose), `migrate` succeeds and the app loads its login page.
- `python manage.py makemigrations --check --dry-run` reports no changes.
- A new test creates a fresh database through `migrate` (not the test runner's shortcut) and checks that each app's main table exists.

## 2. CI so this cannot happen again

Add a GitHub Actions workflow that runs on every push and pull request:

- Install dependencies
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run` (fails if a model changed without a migration)
- `python manage.py migrate` on an empty database
- `python manage.py test tests`
- Dependency vulnerability scan (for example `pip-audit`)

This covers threat model item T9 (dependency scanning).

## 3. Docker end-to-end check

- Run `docker compose up --build` from a clean checkout and confirm the app starts, migrations apply, roles seed, and the login page loads at `http://localhost:8000`.
- Confirm the database port is not exposed outside the compose network (threat model E6).
- Confirm the app refuses to start in production mode with the placeholder `SECRET_KEY` (already working; keep a test for it).
- Document how to create the first admin with a command, with no default account (threat model E5).

## 4. README refresh

The README on GitHub is still the first draft. Update it to match what is built:

- Replace the single `Item` table with `ItemType` and `Unit`, and add `Role`, `Department`, `Term`, and `AuditEvent` to the data model table.
- Update the roles section to describe the `Role` table and `max_active_loans`.
- Update the hold rule: overdue items block new bookings, plus a per-role loan limit. Kit pieces are exempt.
- Remove "MIT (suggested). Add a `LICENSE` file" (the file exists) and "(to be written)" next to `CONTRIBUTING.md`.
- Replace `YOUR-NAME` in the clone URL with `sinan-can-demir`.
- Add a "Status" section stating that v1 is in progress and listing what works and what is deferred (see `V1_PLAN.md`).
- Link to `PATCH_NOTES_001.md` through `003`, `V1_PLAN.md`, and `THREAT_MODEL.md`.
- Add a roadmap that matches `V1_PLAN.md`.

## 5. Small fixes

- Create `static/` with a `.gitkeep` file to remove the `staticfiles.W004` warning.
- Add `SECURITY.md` with a private way to report vulnerabilities (GitHub private vulnerability reporting is enough to start) and a note on what response to expect.
- Move `project-tree.txt` into `docs/` or update it to match the actual files, since the real tree now differs (no `docs/` contents listed, `audit` and `departments` apps added).

## 6. Test gaps to close

The threat model lists security tests. Check which exist in `tests/` and add the missing ones:

- A student cannot open another student's booking, fee, or loan by changing the URL.
- A student cannot reach any admin or staff page.
- A student cannot change their own role through a crafted form submission.
- Two simultaneous requests for the last available unit produce one booking.
- An edited or deleted condition log entry is refused.
- Login and password reset messages are the same for known and unknown accounts.

Note any that are already covered rather than writing duplicates.

## 7. Out of scope for this patch

No new features. Everything in the "Deferred" list of `V1_PLAN.md` stays deferred (waitlist, kits, maintenance, QR, ID checks, reports, rollover, pickup logistics, extra account types, real multi-department behavior).

## 8. Suggested commit order

1. Add migrations, with a test that builds the database through `migrate`.
2. Add CI.
3. Verify Docker end to end and fix anything it finds.
4. Add `static/.gitkeep` and `SECURITY.md`.
5. Refresh the README and tidy `project-tree.txt`.
6. Add the missing security tests.

Each step should leave the project passing its checks.

## 9. Open questions

- Should the role seed and default department be created by a data migration (automatic, runs once) or by the startup command only?
- Which CI checks should block merging, and which should only warn?
- Should the first release be tagged once migrations, CI, and the Docker check pass, even though v1 screens are still rough?
