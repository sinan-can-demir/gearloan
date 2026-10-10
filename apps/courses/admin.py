from django.contrib import admin

from .models import Course, Enrollment, Term


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date", "active", "department"]
    list_filter = ["active", "department"]
    list_editable = ["active"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "term", "term_label", "department", "enrollment_count"]
    list_filter = ["term", "department"]
    search_fields = ["name"]

    def enrollment_count(self, obj):
        return obj.enrollments.count()
    enrollment_count.short_description = "Enrolled"


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["user", "course", "enrolled_at"]
    list_filter = ["course__term"]
    search_fields = ["user__email", "user__username", "course__name"]
    raw_id_fields = ["user", "course"]
