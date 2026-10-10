import csv
import io

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Term

from .base import ImportResult, RosterImporter

REQUIRED_COLUMNS = {"email", "course_name", "term"}


class CsvRosterImporter(RosterImporter):
    """Import enrollments from a CSV with columns: email, course_name, term.

    Optional columns: term_start, term_end (ISO dates).
    If provided, a Term record is found or created with those dates.
    """

    def import_roster(self, source) -> ImportResult:
        if isinstance(source, (str, bytes)):
            text = source.decode() if isinstance(source, bytes) else source
            reader = csv.DictReader(io.StringIO(text))
        else:
            reader = csv.DictReader(source)

        result = ImportResult()

        for row_num, row in enumerate(reader, start=2):
            missing = REQUIRED_COLUMNS - set(row.keys())
            if missing:
                result.errors.append(f"Row {row_num}: missing columns {missing}")
                continue

            email = row["email"].strip().lower()
            course_name = row["course_name"].strip()
            term_name = row["term"].strip()

            if not email or not course_name or not term_name:
                result.errors.append(f"Row {row_num}: empty field(s)")
                continue

            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                result.errors.append(f"Row {row_num}: no user with email {email!r}")
                continue

            term_start = row.get("term_start", "").strip() or None
            term_end = row.get("term_end", "").strip() or None

            term_defaults = {}
            if term_start:
                term_defaults["start_date"] = term_start
            if term_end:
                term_defaults["end_date"] = term_end

            term, _ = Term.objects.get_or_create(
                name=term_name, defaults=term_defaults
            )
            course, _ = Course.objects.get_or_create(
                name=course_name, term=term,
                defaults={"term_label": term_name},
            )
            _, created = Enrollment.objects.get_or_create(user=user, course=course)

            if created:
                result.created += 1
            else:
                result.skipped += 1

        return result
