import csv
import io

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment

from .base import ImportResult, RosterImporter

REQUIRED_COLUMNS = {"email", "course_name", "term"}


class CsvRosterImporter(RosterImporter):
    """Import enrollments from a CSV with columns: email, course_name, term."""

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
            term = row["term"].strip()

            if not email or not course_name or not term:
                result.errors.append(f"Row {row_num}: empty field(s)")
                continue

            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                result.errors.append(f"Row {row_num}: no user with email {email!r}")
                continue

            course, _ = Course.objects.get_or_create(name=course_name, term=term)
            _, created = Enrollment.objects.get_or_create(user=user, course=course)

            if created:
                result.created += 1
            else:
                result.skipped += 1

        return result
