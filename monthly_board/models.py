"""
Data models for Monthly Plan Board.
"""
from dataclasses import dataclass
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
    """A plan assigned to a specific month with optional date range."""
    id: str
    name: str
    year: int
    month: int  # 1-12
    plan_type: PlanType
    color: str
    start_day: Optional[int] = None  # 1-31
    end_day: Optional[int] = None    # 1-31

    @classmethod
    def create(
        cls,
        name: str,
        year: int,
        month: int,
        plan_type: PlanType = PlanType.OTHER,
        color: Optional[str] = None,
        start_day: Optional[int] = None,
        end_day: Optional[int] = None
    ) -> "Plan":
        if color is None:
            color_index = hash(name) % len(PLAN_COLORS)
            color = PLAN_COLORS[color_index]

        return cls(
            id=str(uuid.uuid4()),
            name=name,
            year=year,
            month=month,
            plan_type=plan_type,
            color=color,
            start_day=start_day,
            end_day=end_day
        )

    def get_date_display(self) -> str:
        """Get a display string for the date range."""
        if self.start_day and self.end_day:
            if self.start_day == self.end_day:
                return f"{self.month}/{self.start_day}"
            return f"{self.month}/{self.start_day} - {self.month}/{self.end_day}"
        elif self.start_day:
            return f"{self.month}/{self.start_day}"
        return ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
            "month": self.month,
            "plan_type": self.plan_type.value,
            "color": self.color,
            "start_day": self.start_day,
            "end_day": self.end_day
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        return cls(
            id=data["id"],
            name=data["name"],
            year=data["year"],
            month=data["month"],
            plan_type=PlanType(data["plan_type"]),
            color=data["color"],
            start_day=data.get("start_day"),
            end_day=data.get("end_day")
        )


@dataclass
class BoardState:
    """The complete board state containing all plans."""
    plans: list[Plan]
    current_year: int

    @classmethod
    def create(cls, year: int) -> "BoardState":
        return cls(plans=[], current_year=year)

    def add_plan(self, plan: Plan) -> None:
        """Add a plan to the board."""
        self.plans.append(plan)

    def remove_plan(self, plan_id: str) -> bool:
        """Remove a plan by ID."""
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
        """Get all plans for a specific month."""
        return [p for p in self.plans if p.year == year and p.month == month]

    def to_dict(self) -> dict:
        return {
            "plans": [plan.to_dict() for plan in self.plans],
            "current_year": self.current_year
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BoardState":
        from datetime import date
        state = cls(
            plans=[],
            current_year=data.get("current_year", date.today().year)
        )
        state.plans = [Plan.from_dict(p) for p in data.get("plans", [])]
        return state
