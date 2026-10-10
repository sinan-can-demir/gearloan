from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ImportResult:
    created: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self):
        return self.created + self.skipped

    def __str__(self):
        return (
            f"Imported {self.created} enrollments, "
            f"skipped {self.skipped}, "
            f"{len(self.errors)} error(s)."
        )


class RosterImporter(ABC):
    """Abstract base for roster importers (CSV, Canvas, Banner, …)."""

    @abstractmethod
    def import_roster(self, source) -> ImportResult:
        """Read enrollments from *source* and persist them. Return a result summary."""
