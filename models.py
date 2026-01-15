"""
Data models for Long Plan Desktop App.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid


class ItemStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Duration(Enum):
    THREE_MONTHS = "3months"
    SIX_MONTHS = "6months"
    ONE_YEAR = "1year"

    @property
    def label(self) -> str:
        labels = {
            "3months": "3개월",
            "6months": "6개월",
            "1year": "1년"
        }
        return labels[self.value]

    @property
    def weeks(self) -> int:
        weeks_map = {
            "3months": 12,
            "6months": 26,
            "1year": 52
        }
        return weeks_map[self.value]


@dataclass
class Item:
    """A single task item within a phase."""
    id: str
    name: str
    phase_id: str
    order: int
    status: ItemStatus = ItemStatus.PENDING

    @classmethod
    def create(cls, name: str, phase_id: str, order: int) -> "Item":
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            phase_id=phase_id,
            order=order
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phase_id": self.phase_id,
            "order": self.order,
            "status": self.status.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(
            id=data["id"],
            name=data["name"],
            phase_id=data["phase_id"],
            order=data["order"],
            status=ItemStatus(data["status"])
        )


@dataclass
class Phase:
    """A major phase in the plan (3-5 phases total)."""
    id: str
    name: str
    order: int
    items: list[Item] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, order: int) -> "Phase":
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            order=order
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "items": [item.to_dict() for item in self.items]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Phase":
        phase = cls(
            id=data["id"],
            name=data["name"],
            order=data["order"]
        )
        phase.items = [Item.from_dict(item) for item in data.get("items", [])]
        return phase


@dataclass
class Plan:
    """The complete plan containing all phases and items."""
    id: str
    goal: str
    duration: Duration
    weekly_hours: int
    phases: list[Phase] = field(default_factory=list)

    @classmethod
    def create(cls, goal: str, duration: Duration, weekly_hours: int) -> "Plan":
        return cls(
            id=str(uuid.uuid4()),
            goal=goal,
            duration=duration,
            weekly_hours=weekly_hours
        )

    def get_current_item(self) -> Optional[Item]:
        """Get the first pending item across all phases in order."""
        for phase in sorted(self.phases, key=lambda p: p.order):
            for item in sorted(phase.items, key=lambda i: i.order):
                if item.status == ItemStatus.PENDING:
                    return item
        return None

    def get_current_phase(self) -> Optional[Phase]:
        """Get the phase containing the current item."""
        current_item = self.get_current_item()
        if current_item:
            for phase in self.phases:
                if phase.id == current_item.phase_id:
                    return phase
        return None

    def get_progress(self) -> tuple[int, int]:
        """Get (completed_count, total_count) for progress tracking."""
        total = 0
        completed = 0
        for phase in self.phases:
            for item in phase.items:
                total += 1
                if item.status == ItemStatus.COMPLETED:
                    completed += 1
        return completed, total

    def complete_current(self) -> bool:
        """Mark the current item as completed. Returns True if successful."""
        current = self.get_current_item()
        if current:
            current.status = ItemStatus.COMPLETED
            return True
        return False

    def skip_current(self) -> bool:
        """Move the current item to the end of its phase. Returns True if successful."""
        current = self.get_current_item()
        if current:
            for phase in self.phases:
                if phase.id == current.phase_id:
                    max_order = max(i.order for i in phase.items)
                    current.order = max_order + 1
                    return True
        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "duration": self.duration.value,
            "weekly_hours": self.weekly_hours,
            "phases": [phase.to_dict() for phase in self.phases]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        plan = cls(
            id=data["id"],
            goal=data["goal"],
            duration=Duration(data["duration"]),
            weekly_hours=data["weekly_hours"]
        )
        plan.phases = [Phase.from_dict(phase) for phase in data.get("phases", [])]
        return plan
