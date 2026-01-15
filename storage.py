"""
Local JSON storage for Long Plan Desktop App.
"""
import json
import os
from pathlib import Path
from typing import Optional

from models import Plan


class Storage:
    """Handles persistence of plan data to local JSON file."""

    def __init__(self, filename: str = "plan_data.json"):
        # Store in user's app data directory
        app_data = Path(os.getenv("APPDATA", Path.home())) / "LongPlan"
        app_data.mkdir(parents=True, exist_ok=True)
        self.filepath = app_data / filename

    def save(self, plan: Plan) -> None:
        """Save the plan to JSON file."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)

    def load(self) -> Optional[Plan]:
        """Load the plan from JSON file. Returns None if no plan exists."""
        if not self.filepath.exists():
            return None
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Plan.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def clear(self) -> None:
        """Delete the stored plan."""
        if self.filepath.exists():
            self.filepath.unlink()

    def exists(self) -> bool:
        """Check if a plan exists."""
        return self.filepath.exists()
