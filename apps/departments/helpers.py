"""
Department-scoped query helpers.

In v1 there is one department and no filtering is applied. All queries
route through get_queryset() so turning on multi-department scoping later
is a single-file change.
"""

from functools import cache

from .models import Department


@cache
def get_default_department() -> Department:
    dept, _ = Department.objects.get_or_create(
        slug="default",
        defaults={"name": "Music Department"},
    )
    return dept


def scoped_qs(model_class, department=None):
    """Return a queryset for *model_class*, optionally filtered by department.

    In v1 the department parameter is ignored and all objects are returned.
    When multi-department is enabled, pass the current department here.
    """
    return model_class.objects.all()
