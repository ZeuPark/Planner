"""
Data models for Monthly Plan Board.
"""
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional
import uuid


class PlanType(Enum):
    PROJECT = "project"
    STUDY = "study"
    PREPARATION = "preparation"
    EXERCISE = "exercise"
    REST = "rest"
    OTHER = "other"

    @property
    def label(self) -> str:
        labels = {
            "project": "프로젝트",
            "study": "학업",
            "preparation": "준비",
            "exercise": "운동",
            "rest": "휴식",
            "other": "기타"
        }
        return labels[self.value]


# Predefined color palette for plans
PLAN_COLORS = [
    "#4a9eff",  # Blue
    "#f472b6",  # Pink
    "#4ade80",  # Green
    "#fbbf24",  # Yellow
    "#a78bfa",  # Purple
    "#fb923c",  # Orange
    "#22d3d8",  # Cyan
    "#f87171",  # Red
]


@dataclass
class Plan:
    """A plan block spanning multiple days."""
    id: str
    name: str
    start_date: date
    end_date: date
    plan_type: PlanType
    color: str

    @classmethod
    def create(
        cls,
        name: str,
        start_date: date,
        end_date: date,
        plan_type: PlanType = PlanType.OTHER,
        color: Optional[str] = None
    ) -> "Plan":
        if color is None:
            # Auto-assign color based on hash of name
            color_index = hash(name) % len(PLAN_COLORS)
            color = PLAN_COLORS[color_index]

        return cls(
            id=str(uuid.uuid4()),
            name=name,
            start_date=start_date,
            end_date=end_date,
            plan_type=plan_type,
            color=color
        )

    def spans_date(self, d: date) -> bool:
        """Check if this plan spans the given date."""
        return self.start_date <= d <= self.end_date

    def get_duration_days(self) -> int:
        """Get the total duration in days."""
        return (self.end_date - self.start_date).days + 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "plan_type": self.plan_type.value,
            "color": self.color
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        return cls(
            id=data["id"],
            name=data["name"],
            start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]),
            plan_type=PlanType(data["plan_type"]),
            color=data["color"]
        )


@dataclass
class BoardState:
    """The complete board state containing all plans."""
    plans: list[Plan]

    @classmethod
    def create(cls) -> "BoardState":
        return cls(plans=[])

    def add_plan(self, plan: Plan) -> None:
        """Add a plan to the board."""
        self.plans.append(plan)

    def remove_plan(self, plan_id: str) -> bool:
        """Remove a plan by ID. Returns True if found and removed."""
        for i, plan in enumerate(self.plans):
            if plan.id == plan_id:
                self.plans.pop(i)
                return True
        return False

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Get a plan by ID."""
        for plan in self.plans:
            if plan.id == plan_id:
                return plan
        return None

    def update_plan(self, plan_id: str, **kwargs) -> bool:
        """Update a plan's attributes."""
        plan = self.get_plan(plan_id)
        if plan:
            for key, value in kwargs.items():
                if hasattr(plan, key):
                    setattr(plan, key, value)
            return True
        return False

    def get_plans_for_month(self, year: int, month: int) -> list[Plan]:
        """Get all plans that overlap with the given month."""
        from calendar import monthrange
        month_start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        month_end = date(year, month, last_day)

        return [
            plan for plan in self.plans
            if plan.start_date <= month_end and plan.end_date >= month_start
        ]

    def to_dict(self) -> dict:
        return {
            "plans": [plan.to_dict() for plan in self.plans]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BoardState":
        state = cls(plans=[])
        state.plans = [Plan.from_dict(p) for p in data.get("plans", [])]
        return state
