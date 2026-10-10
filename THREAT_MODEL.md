# Threat model: GearLoan

Status: first draft, written before most of the code exists. Review it again when the booking, check-out, and fee features are built, and whenever a deferred feature (photos, ID checks, QR, multi-department, connectors) moves into scope.

Method: assets, actors, trust boundaries, then threats grouped by STRIDE (spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege). Each threat has a mitigation and a version tag (v1 means required before v1 is called done).

## 1. What we are protecting

| Asset | Why it matters |
|-------|----------------|
| Student and faculty records (names, emails, enrollments) | Student data. Colleges have privacy duties (in the US, FERPA). |
| Fee records | A wrong or altered fee is a financial dispute for a student. |
| Inventory and condition history | Evidence in damage disputes. Hundreds or thousands of dollars of gear. |
| Admin accounts | An admin can approve, waive fees, change rules, and import data. |
| Audit log | Only trustworthy if nobody can edit it. |
| Photos and ID-check records (deferred) | Photos of people and records of ID checks are sensitive. |
| Email sender identity | Spoofed or hijacked notification email is a phishing path. |
| The server and database | Self-hosted by departments with small IT teams. |

## 2. Actors

| Actor | Trust |
|-------|-------|
| Student, guest | Low. Authenticated but may be careless or dishonest. |
| Faculty | Medium. Longer loans, fewer approvals. |
| Admin and student-worker staff | High. Can change money-related and rule-related data. |
| Site operator (department IT) | Highest. Controls the server, secrets, and backups. |
| Outsider on the internet | None. Can reach the login page and public URLs. |
| Malicious insider (student worker, faculty) | Authenticated, abusing legitimate access. |
| Contributor or dependency author | Supply chain. Can introduce bad code. |

## 3. Trust boundaries

1. Internet to web app (login, forms, CSV uploads).
2. Web app to database.
3. Web app to email server.
4. Web app to file storage (CSV uploads, later photos).
5. Role boundary inside the app: borrower versus staff versus admin.
6. Department boundary (when multi-department is on).
7. Future: connectors to university systems (Canvas, billing).

## 4. Key assumptions

- Departments self-host, so deployment quality varies. Defaults must be safe.
- The app will often run behind the university network or single sign-on, but it must not assume this.
- Passwords are the weakest link in v1. Universities usually have single sign-on, so SSO support should be planned.
- Data about students is regulated and shared by the college, not owned by the department or by this project.

## 5. Threats and mitigations

### Spoofing (pretending to be someone)

| # | Threat | Mitigation | Tag |
|---|--------|------------|-----|
| S1 | Attacker guesses or reuses a password and logs in as a student or admin | Django password validators, rate limiting and lockout on login, strong password hashing (Django default), optional two-factor for admin roles | v1 (limits), later (2FA) |
| S2 | Attacker takes over an admin account and waives fees or approves gear | Require two-factor for admin and staff roles when enabled. Log every admin action. Alert on unusual admin activity. | v1 (logging), later (2FA) |
| S3 | Someone borrows gear while pretending to be another person at check-out | Admin checks photo ID at check-out and records that the check happened. Required for high-value gear. | later (ID checks) |
| S4 | Spoofed emails that look like they come from the system (phishing) | Send from a verified domain with SPF, DKIM, and DMARC. Emails never ask for passwords or payment. Emails link to the app instead of carrying actions. | v1 (docs and defaults) |
| S5 | Password reset used to take over an account | Reset links expire quickly and are single use. Reset emails do not reveal whether an account exists. | v1 |

### Tampering (changing things that should not change)

| # | Threat | Mitigation | Tag |
|---|--------|------------|-----|
| T1 | Student edits a booking, due date, or fee through direct requests | Server-side permission checks on every action. Never trust hidden form fields. Fees are computed on the server. | v1 |
| T2 | Student extends a loan past the allowed limit or around another reservation | Extension rules enforced in the service layer, with a database-level check where possible. Tests cover it. | v1 |
| T3 | Two requests book the same unit at the same time (race condition) | Database transactions and row locking when approving or checking out a unit. Unique constraint on one active booking per unit. | v1 |
| T4 | Malicious or malformed CSV changes enrollments or inventory in bulk | Admin-only import, dry-run preview before commit, validation of every row, size limit, import logged with the file name and a row count. | v1 |
| T5 | CSV formula injection (cells starting with `=`, `+`, `-`, `@` run as formulas when an admin opens an export in Excel) | Escape or prefix risky cells in every CSV export. | v1 (with reports) |
| T6 | Admin or staff quietly changes item rules (for example lowers replacement cost) to cheat the system | Rule changes require admin role and are written to the audit log with before and after values. | v1 |
| T7 | Tampering with unit condition logs after a dispute starts | Condition logs are append-only. Corrections are new entries that reference the old one. | v1 |
| T8 | Cross-site request forgery makes an admin perform an action | Django CSRF protection on all state-changing requests. State changes never use GET. | v1 |
| T9 | Malicious dependency or compromised package | Pinned versions, dependency scanning in CI, minimal dependencies, review before adding any new one. | v1 |

### Repudiation (denying an action)

| # | Threat | Mitigation | Tag |
|---|--------|------------|-----|
| R1 | Student says they never received the cello, or that it was already damaged | Condition log at check-out and check-in, signed by staff, with timestamps. Photos later. | v1 (logs), later (photos) |
| R2 | Admin denies waiving a fee or overriding a hold | Append-only audit log with user, time, reason, before and after values. | v1 |
| R3 | Audit log is edited or deleted | No edit or delete in the interface. Database permissions limit the app account. Operators may ship the log elsewhere. | v1 (interface), later (shipping) |
| R4 | Student claims they never got a reminder or overdue email | Log that the email was sent, to which address, and when. | v1 |

### Information disclosure (data leaking)

| # | Threat | Mitigation | Tag |
|---|--------|------------|-----|
| I1 | Student sees another student's bookings, fees, or contact details by changing an ID in the URL | Object-level permission checks on every view. Use unguessable identifiers in URLs where practical. Tests for this specifically. | v1 |
| I2 | Borrower screens show who else has the item or who is on the waitlist | Show availability only, not names. | v1 |
| I3 | Student worker sees more than their role needs (fees, full roster) | Staff roles limited to check-in and check-out unless granted more. Role permissions are explicit. | v1 |
| I4 | Reports or exports leak student data | Reports are admin-only, filtered by department, and exports are logged. | v1 (with reports) |
| I5 | Secrets leak (secret key, database password, email credentials) | Secrets only in environment variables. `.env` in `.gitignore`. A `.env.example` with no real values. Debug mode off by default in production settings. | v1 |
| I6 | Database or backups leave the server unencrypted | Document encrypted backups and disk encryption. Use TLS between the app and a remote database. | v1 (docs) |
| I7 | Photos and ID-check records exposed through public URLs | Private file storage, served only after a permission check, never from a public folder. Do not store images of IDs. | later |
| I8 | Error pages and logs reveal stack traces, emails, or tokens | Debug off in production. Do not log passwords, tokens, or full request bodies. | v1 |
| I9 | Data retained longer than needed | Retention setting for old bookings, photos, and audit entries, with a deletion tool. Colleges will have their own policy. | later |
| I10 | Account enumeration through login or password reset messages | Same message for known and unknown accounts. | v1 |

### Denial of service (making the system unavailable)

| # | Threat | Mitigation | Tag |
|---|--------|------------|-----|
| D1 | Login or request flooding | Rate limiting at the reverse proxy and on login. | v1 (docs and login), later (broader) |
| D2 | One user hoards gear by booking many items or the same unit repeatedly | Hold rule, `max_active_loans`, and limits on pending requests per user. | v1 |
| D3 | Waitlist abuse: joining every list to block others | Limit waitlist entries per user, claim windows that expire. | later |
| D4 | Large or malicious CSV upload exhausts memory | File size limit, row limit, streaming parse, upload only for admins. | v1 |
| D5 | Email flood (a bug or abuse sends thousands of messages) | Send in batches, cap sends per user per day, queue with retries and a kill switch. | v1 |
| D6 | Database full or server down with no backups | Documented backup and restore. Health check in Docker. | v1 (docs) |

### Elevation of privilege (getting more access)

| # | Threat | Mitigation | Tag |
|---|--------|------------|-----|
| E1 | Student reaches admin pages by guessing URLs | Every admin view checks the role on the server. Default deny. | v1 |
| E2 | User changes their own role, for example through a profile form that exposes the role field | Role is never editable from borrower forms. Only admins change roles, and changes are logged. | v1 |
| E3 | Admin of one department sees or edits another department's data | Department filter on every query through one helper. Tests with two departments. | v1 (helper), later (full) |
| E4 | Staff role with check-out rights approves their own request | Approval and check-out of one's own booking requires a different person. | v1 |
| E5 | First admin account created with a default or well-known password | No default accounts. First admin is created through a command during setup. | v1 |
| E6 | Insecure defaults in the Docker setup (open database port, debug on, default secrets) | Database not exposed outside the compose network. Debug off. Setup fails if the secret key is the placeholder. | v1 |
| E7 | Injection (SQL, template, command) | Use the Django ORM, escape output in templates, no shell calls with user input. | v1 |
| E8 | File upload runs as code (when photos arrive) | Validate type and size, rename files, store outside the web root, serve with a safe content type. | later |

## 6. Abuse by legitimate users

Some of the most likely problems are not hackers.

| Scenario | Mitigation |
|----------|------------|
| A student keeps gear past the due date and ignores emails | Overdue hold, escalating reminders, fees, admin follow-up tools |
| A student reports an item lost when they just kept it | Lost reports must be verified by an admin, and the full replacement fee applies if confirmed |
| A student reports damage that was already there to avoid a charge | Check-out condition log and photos |
| A staff member waives fees for friends | Waiver needs a reason, shows in the audit log, and appears in reports for review |
| Someone books gear they are not eligible for by changing course enrollment | Enrollment comes only from an admin-controlled import, not from the borrower |
| Gear is checked out to one person and used by another | Student ID check, and a rule that the borrower is responsible |

## 7. Data protection and privacy

- Collect only what is needed: name, email, role, and enrollments.
- Student data comes from the college. Operators should confirm with their registrar or IT office that using it this way is allowed.
- Make retention configurable (bookings, audit entries, photos). Provide a way to delete or anonymize a former student's data while keeping the audit trail intact.
- Document what data the app stores so a college privacy office can review it.
- If the app is used in other countries, the operator may owe additional duties (such as GDPR). The project does not give legal advice.

## 8. Supply chain and project risks

- Keep dependencies few and pinned. Run a dependency vulnerability scan in CI.
- Review every contribution. Require review for changes to permissions, fees, and the audit log.
- Publish a `SECURITY.md` with a private way to report vulnerabilities and what to expect in response.
- Sign release tags or publish checksums for Docker images.
- Document a way to update safely, since self-hosted installs tend to fall behind on patches.

## 9. Highest priority for v1

1. Server-side permission checks everywhere, with tests for borrowers reading or changing each other's data (I1, E1, E2).
2. Safe booking logic that survives simultaneous requests (T3).
3. Append-only audit log and condition logs (R1, R2, R3, T7).
4. Safe defaults in Docker and settings, with no default admin and no debug mode (E5, E6, I5).
5. Careful CSV import with dry-run, limits, and logging (T4, D4).
6. Login protections and safe password reset (S1, S5, I10).
7. Email setup guidance, including SPF, DKIM, and DMARC (S4).
8. A `SECURITY.md` and dependency scanning in CI (T9).

## 10. Security tests to write

- A student cannot open another student's booking, fee, or loan by changing the URL.
- A student cannot reach any admin or staff page.
- A student cannot change their own role by crafting a form submission.
- Two simultaneous requests for the last available unit produce one booking.
- A CSV with oversized, malformed, or formula-starting cells is rejected or neutralized.
- A fee cannot be created, changed, or waived without the right role, and every change writes an audit event.
- An edited or deleted condition log entry is refused.
- Password reset and login messages are the same for known and unknown accounts.
- With two departments, an admin in one cannot read or change the other's data.

## 11. Open questions

- Will most installs use single sign-on? If so, support for it (SAML or OpenID Connect) should move earlier, since it removes the password risks.
- Does the project want to claim any compliance (such as FERPA readiness), or just document the data it stores?
- Should admin two-factor be required or optional in v1?
- How long should the project promise to support security fixes for older versions?
- Who handles reports sent to `SECURITY.md`, and how fast?

## 12. When to update this document

Review this threat model when any of these happen: photos or ID checks are added, QR scanning is added, a university connector (Canvas, billing) is added, multi-department is turned on for real, or a security issue is reported.
