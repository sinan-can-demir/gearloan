import textwrap

from django.test import TestCase

from apps.accounts.models import User
from apps.courses.importers.csv_importer import CsvRosterImporter
from apps.courses.models import Course, Enrollment, Term


class CsvRosterImporterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student1",
            email="student1@college.edu",
            password="pw",
        )
        self.importer = CsvRosterImporter()

    def _csv(self, content):
        return textwrap.dedent(content).strip()

    def test_creates_enrollment(self):
        result = self.importer.import_roster(self._csv("""
            email,course_name,term
            student1@college.edu,Cello I,Fall 2026
        """))
        self.assertEqual(result.created, 1)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(len(result.errors), 0)
        self.assertTrue(
            Enrollment.objects.filter(user=self.user, course__name="Cello I").exists()
        )

    def test_skips_duplicate_enrollment(self):
        csv = self._csv("""
            email,course_name,term
            student1@college.edu,Cello I,Fall 2026
        """)
        self.importer.import_roster(csv)
        result = self.importer.import_roster(csv)
        self.assertEqual(result.created, 0)
        self.assertEqual(result.skipped, 1)

    def test_unknown_email_produces_error(self):
        result = self.importer.import_roster(self._csv("""
            email,course_name,term
            nobody@college.edu,Cello I,Fall 2026
        """))
        self.assertEqual(result.created, 0)
        self.assertEqual(len(result.errors), 1)

    def test_missing_columns_produce_error(self):
        result = self.importer.import_roster(self._csv("""
            email,course_name
            student1@college.edu,Cello I
        """))
        self.assertGreater(len(result.errors), 0)

    def test_creates_term_and_course_if_missing(self):
        self.importer.import_roster(self._csv("""
            email,course_name,term
            student1@college.edu,New Course,Spring 2027
        """))
        self.assertTrue(Term.objects.filter(name="Spring 2027").exists())
        self.assertTrue(Course.objects.filter(name="New Course").exists())

    def test_creates_term_with_dates_when_provided(self):
        self.importer.import_roster(self._csv("""
            email,course_name,term,term_start,term_end
            student1@college.edu,Cello I,Fall 2026,2026-09-01,2026-12-15
        """))
        term = Term.objects.get(name="Fall 2026")
        self.assertEqual(str(term.start_date), "2026-09-01")
        self.assertEqual(str(term.end_date), "2026-12-15")
