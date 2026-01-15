"""
Local JSON storage for Monthly Plan Board.
"""
import json
import os
from pathlib import Path
from typing import Optional

from models import BoardState


class Storage:
    """Handles persistence of board state to local JSON file."""

    def __init__(self, filename: str = "monthly_board_data.json"):
        # Store in user's app data directory
        app_data = Path(os.getenv("APPDATA", Path.home())) / "MonthlyPlanBoard"
        app_data.mkdir(parents=True, exist_ok=True)
        self.filepath = app_data / filename

    def save(self, state: BoardState) -> None:
        """Save the board state to JSON file."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

    def load(self) -> BoardState:
        """Load the board state from JSON file. Returns empty state if none exists."""
        if not self.filepath.exists():
            return BoardState.create()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return BoardState.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return BoardState.create()

    def clear(self) -> None:
        """Delete the stored state."""
        if self.filepath.exists():
            self.filepath.unlink()
