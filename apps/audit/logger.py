"""
Thin wrapper around AuditEvent.objects.create.

All callers import log_event from here so the details of what gets stored
are in one place.
"""

from .models import AuditEvent


def log_event(event_type: str, actor=None, target=None, details=None, department=None):
    """Create an AuditEvent record.

    Args:
        event_type: One of the AuditEvent.* constants (or any string).
        actor: The User who triggered the event, or None for system events.
        target: A model instance to record as (target_type, target_id).
        details: A JSON-serialisable dict of extra context.
        department: The Department this event belongs to.
    """
    target_type = ""
    target_id = None
    if target is not None:
        target_type = target.__class__.__name__
        target_id = getattr(target, "pk", None)

    if department is None and actor is not None:
        # Best-effort: pull department from actor's most common booking
        pass

    AuditEvent.objects.create(
        actor=actor,
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
        department=department,
    )
