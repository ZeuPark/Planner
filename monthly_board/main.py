"""
Monthly Plan Board
개인용 월 단위 플랜 캘린더

A personal monthly planning board that shows plans as visual blocks.
"""
import sys
from calendar import monthrange
from datetime import date, timedelta
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFrame, QDialog, QLineEdit,
    QComboBox, QDateEdit, QSizePolicy, QSpacerItem, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QDate, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QBrush

from models import Plan, PlanType, BoardState, PLAN_COLORS
from storage import Storage
from styles import STYLESHEET, COLORS


class PlanBlock(QWidget):
    """A visual block representing a plan on the calendar."""

    clicked = Signal(str)  # Emits plan_id
    delete_requested = Signal(str)  # Emits plan_id

    def __init__(self, plan: Plan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.setFixedHeight(24)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"{plan.name}\n{plan.start_date} ~ {plan.end_date}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw rounded rectangle
        color = QColor(self.plan.color)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 6, 6)

        # Draw text
        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont("Segoe UI", 10)
        font.setBold(True)
        painter.setFont(font)

        text_rect = self.rect().adjusted(10, 0, -10, 0)
        metrics = QFontMetrics(font)
        elided = metrics.elidedText(self.plan.name, Qt.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, elided)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.plan.id)
        elif event.button() == Qt.RightButton:
            self.delete_requested.emit(self.plan.id)


class CalendarCell(QFrame):
    """A single cell in the calendar grid."""

    clicked = Signal(date)
    drag_started = Signal(date)
    drag_ended = Signal(date)

    def __init__(self, cell_date: date, is_current_month: bool, is_today: bool, is_weekend: bool):
        super().__init__()
        self.cell_date = cell_date
        self.is_current_month = is_current_month
        self.is_today = is_today
        self.is_weekend = is_weekend
        self.plans_layout = None

        self._setup_ui()

    def _setup_ui(self):
        if self.is_today:
            self.setObjectName("calendarCellToday")
        elif not self.is_current_month:
            self.setObjectName("calendarCellOtherMonth")
        elif self.is_weekend:
            self.setObjectName("calendarCellWeekend")
        else:
            self.setObjectName("calendarCell")

        self.setMinimumSize(100, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Date number
        date_label = QLabel(str(self.cell_date.day))
        if self.is_today:
            date_label.setObjectName("dateNumberToday")
        else:
            date_label.setObjectName("dateNumber")

        if not self.is_current_month:
            date_label.setStyleSheet(f"color: {COLORS['text_muted']};")

        layout.addWidget(date_label)

        # Plans container
        self.plans_container = QWidget()
        self.plans_layout = QVBoxLayout(self.plans_container)
        self.plans_layout.setContentsMargins(0, 0, 0, 0)
        self.plans_layout.setSpacing(2)
        layout.addWidget(self.plans_container)

        layout.addStretch()

    def add_plan_block(self, plan: Plan, is_start: bool, is_end: bool, span_days: int):
        """Add a plan block to this cell."""
        block = PlanBlock(plan, self)

        # Only show on start day for multi-day plans
        if is_start or span_days == 1:
            self.plans_layout.addWidget(block)
            return block
        return None

    def clear_plans(self):
        """Remove all plan blocks."""
        while self.plans_layout.count():
            child = self.plans_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_current_month:
            self.drag_started.emit(self.cell_date)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_current_month:
            self.drag_ended.emit(self.cell_date)
        super().mouseReleaseEvent(event)


class AddPlanDialog(QDialog):
    """Dialog for adding a new plan."""

    def __init__(self, start_date: date, end_date: date, parent=None):
        super().__init__(parent)
        self.start_date = start_date
        self.end_date = end_date
        self.selected_color = PLAN_COLORS[0]
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("플랜 추가")
        self.setFixedSize(400, 380)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Title
        title = QLabel("새 플랜")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Name input
        name_label = QLabel("플랜 이름")
        name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("플랜 이름을 입력하세요")
        layout.addWidget(self.name_input)

        # Date range
        dates_layout = QHBoxLayout()
        dates_layout.setSpacing(16)

        start_container = QVBoxLayout()
        start_label = QLabel("시작")
        start_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        start_container.addWidget(start_label)
        self.start_edit = QDateEdit()
        self.start_edit.setDate(QDate(self.start_date.year, self.start_date.month, self.start_date.day))
        self.start_edit.setCalendarPopup(True)
        start_container.addWidget(self.start_edit)
        dates_layout.addLayout(start_container)

        end_container = QVBoxLayout()
        end_label = QLabel("종료")
        end_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        end_container.addWidget(end_label)
        self.end_edit = QDateEdit()
        self.end_edit.setDate(QDate(self.end_date.year, self.end_date.month, self.end_date.day))
        self.end_edit.setCalendarPopup(True)
        end_container.addWidget(self.end_edit)
        dates_layout.addLayout(end_container)

        layout.addLayout(dates_layout)

        # Type selection
        type_label = QLabel("타입")
        type_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        for plan_type in PlanType:
            self.type_combo.addItem(plan_type.label, plan_type)
        layout.addWidget(self.type_combo)

        # Color selection
        color_label = QLabel("색상")
        color_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(color_label)

        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(8)
        self.color_buttons = []

        for i, color in enumerate(PLAN_COLORS):
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid transparent;
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, c=color, b=btn: self._select_color(c, b))
            colors_layout.addWidget(btn)
            self.color_buttons.append(btn)

        colors_layout.addStretch()
        layout.addLayout(colors_layout)

        # Select first color by default
        self._select_color(PLAN_COLORS[0], self.color_buttons[0])

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.add_btn = QPushButton("추가")
        self.add_btn.setObjectName("addButton")
        self.add_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

    def _select_color(self, color: str, button: QPushButton):
        """Select a color and highlight the button."""
        self.selected_color = color

        # Reset all buttons
        for btn in self.color_buttons:
            c = btn.styleSheet().split("background-color: ")[1].split(";")[0]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c};
                    border: 2px solid transparent;
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)

        # Highlight selected
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid white;
                border-radius: 14px;
            }}
        """)

    def get_plan_data(self) -> dict:
        """Get the plan data from the dialog."""
        start_qdate = self.start_edit.date()
        end_qdate = self.end_edit.date()

        return {
            "name": self.name_input.text().strip(),
            "start_date": date(start_qdate.year(), start_qdate.month(), start_qdate.day()),
            "end_date": date(end_qdate.year(), end_qdate.month(), end_qdate.day()),
            "plan_type": self.type_combo.currentData(),
            "color": self.selected_color
        }


class EditPlanDialog(QDialog):
    """Dialog for editing an existing plan."""

    delete_requested = Signal()

    def __init__(self, plan: Plan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.selected_color = plan.color
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("플랜 수정")
        self.setFixedSize(400, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Title
        title = QLabel("플랜 수정")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Name input
        name_label = QLabel("플랜 이름")
        name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setText(self.plan.name)
        layout.addWidget(self.name_input)

        # Date range
        dates_layout = QHBoxLayout()
        dates_layout.setSpacing(16)

        start_container = QVBoxLayout()
        start_label = QLabel("시작")
        start_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        start_container.addWidget(start_label)
        self.start_edit = QDateEdit()
        self.start_edit.setDate(QDate(self.plan.start_date.year, self.plan.start_date.month, self.plan.start_date.day))
        self.start_edit.setCalendarPopup(True)
        start_container.addWidget(self.start_edit)
        dates_layout.addLayout(start_container)

        end_container = QVBoxLayout()
        end_label = QLabel("종료")
        end_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        end_container.addWidget(end_label)
        self.end_edit = QDateEdit()
        self.end_edit.setDate(QDate(self.plan.end_date.year, self.plan.end_date.month, self.plan.end_date.day))
        self.end_edit.setCalendarPopup(True)
        end_container.addWidget(self.end_edit)
        dates_layout.addLayout(end_container)

        layout.addLayout(dates_layout)

        # Type selection
        type_label = QLabel("타입")
        type_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        for plan_type in PlanType:
            self.type_combo.addItem(plan_type.label, plan_type)
            if plan_type == self.plan.plan_type:
                self.type_combo.setCurrentIndex(self.type_combo.count() - 1)
        layout.addWidget(self.type_combo)

        # Color selection
        color_label = QLabel("색상")
        color_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(color_label)

        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(8)
        self.color_buttons = []

        for color in PLAN_COLORS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            is_selected = color == self.plan.color
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid {"white" if is_selected else "transparent"};
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, c=color, b=btn: self._select_color(c, b))
            colors_layout.addWidget(btn)
            self.color_buttons.append(btn)

        colors_layout.addStretch()
        layout.addLayout(colors_layout)

        layout.addStretch()

        # Delete button
        delete_btn = QPushButton("삭제")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(delete_btn)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("저장")
        save_btn.setObjectName("addButton")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _select_color(self, color: str, button: QPushButton):
        """Select a color and highlight the button."""
        self.selected_color = color

        for btn in self.color_buttons:
            c = btn.styleSheet().split("background-color: ")[1].split(";")[0]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c};
                    border: 2px solid transparent;
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid white;
                border-radius: 14px;
            }}
        """)

    def _on_delete(self):
        """Handle delete button click."""
        self.delete_requested.emit()
        self.reject()

    def get_plan_data(self) -> dict:
        """Get the updated plan data from the dialog."""
        start_qdate = self.start_edit.date()
        end_qdate = self.end_edit.date()

        return {
            "name": self.name_input.text().strip(),
            "start_date": date(start_qdate.year(), start_qdate.month(), start_qdate.day()),
            "end_date": date(end_qdate.year(), end_qdate.month(), end_qdate.day()),
            "plan_type": self.type_combo.currentData(),
            "color": self.selected_color
        }


class MonthlyCalendar(QWidget):
    """The main monthly calendar widget with plan blocks."""

    plan_added = Signal(Plan)
    plan_updated = Signal(str, dict)
    plan_deleted = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_date = date.today()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month
        self.cells: dict[date, CalendarCell] = {}
        self.drag_start_date: Optional[date] = None
        self.plans: list[Plan] = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # Header
        header_layout = QHBoxLayout()

        # Navigation
        prev_btn = QPushButton("<")
        prev_btn.setObjectName("navButton")
        prev_btn.clicked.connect(self._prev_month)
        prev_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(prev_btn)

        # Month/Year display
        month_container = QVBoxLayout()
        month_container.setSpacing(2)

        self.month_label = QLabel()
        self.month_label.setObjectName("monthLabel")
        self.month_label.setAlignment(Qt.AlignCenter)
        month_container.addWidget(self.month_label)

        self.year_label = QLabel()
        self.year_label.setObjectName("yearLabel")
        self.year_label.setAlignment(Qt.AlignCenter)
        month_container.addWidget(self.year_label)

        header_layout.addStretch()
        header_layout.addLayout(month_container)
        header_layout.addStretch()

        next_btn = QPushButton(">")
        next_btn.setObjectName("navButton")
        next_btn.clicked.connect(self._next_month)
        next_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(next_btn)

        # Add plan button
        add_btn = QPushButton("+ 플랜 추가")
        add_btn.setObjectName("addButton")
        add_btn.clicked.connect(self._show_add_dialog)
        add_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Day headers
        days_layout = QHBoxLayout()
        days_layout.setSpacing(4)
        day_names = ["월", "화", "수", "목", "금", "토", "일"]

        for day in day_names:
            label = QLabel(day)
            label.setObjectName("dayHeader")
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            days_layout.addWidget(label)

        layout.addLayout(days_layout)

        # Calendar grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.grid_widget, 1)

        self._update_calendar()

    def _update_calendar(self):
        """Update the calendar display for the current month."""
        # Update labels
        month_names = ["", "1월", "2월", "3월", "4월", "5월", "6월",
                      "7월", "8월", "9월", "10월", "11월", "12월"]
        self.month_label.setText(month_names[self.current_month])
        self.year_label.setText(str(self.current_year))

        # Clear existing cells
        self.cells.clear()
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Calculate the first day of the month
        first_day = date(self.current_year, self.current_month, 1)
        # Monday is 0, Sunday is 6
        start_weekday = first_day.weekday()

        # Calculate the starting date (may be in previous month)
        start_date = first_day - timedelta(days=start_weekday)

        # Create 6 weeks of cells
        current = start_date
        for week in range(6):
            for day in range(7):
                is_current_month = current.month == self.current_month
                is_today = current == self.current_date
                is_weekend = day >= 5

                cell = CalendarCell(current, is_current_month, is_today, is_weekend)
                cell.drag_started.connect(self._on_drag_start)
                cell.drag_ended.connect(self._on_drag_end)

                self.grid_layout.addWidget(cell, week, day)
                self.cells[current] = cell

                current += timedelta(days=1)

        # Add plan blocks
        self._update_plan_blocks()

    def _update_plan_blocks(self):
        """Update plan blocks on the calendar."""
        # Clear all plan blocks
        for cell in self.cells.values():
            cell.clear_plans()

        # Get plans for this month
        month_plans = [p for p in self.plans
                      if p.start_date.year == self.current_year and p.start_date.month == self.current_month
                      or p.end_date.year == self.current_year and p.end_date.month == self.current_month
                      or (p.start_date < date(self.current_year, self.current_month, 1)
                          and p.end_date > date(self.current_year, self.current_month, monthrange(self.current_year, self.current_month)[1]))]

        # Add blocks for each plan
        for plan in month_plans:
            for cell_date, cell in self.cells.items():
                if plan.spans_date(cell_date):
                    is_start = cell_date == plan.start_date
                    is_end = cell_date == plan.end_date
                    span = plan.get_duration_days()

                    block = cell.add_plan_block(plan, is_start, is_end, span)
                    if block:
                        block.clicked.connect(self._on_plan_clicked)
                        block.delete_requested.connect(self._on_plan_delete_requested)

    def set_plans(self, plans: list[Plan]):
        """Set the plans to display."""
        self.plans = plans
        self._update_plan_blocks()

    def _prev_month(self):
        """Go to previous month."""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._update_calendar()

    def _next_month(self):
        """Go to next month."""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._update_calendar()

    def _on_drag_start(self, d: date):
        """Handle drag start."""
        self.drag_start_date = d

    def _on_drag_end(self, d: date):
        """Handle drag end - show add dialog."""
        if self.drag_start_date:
            start = min(self.drag_start_date, d)
            end = max(self.drag_start_date, d)
            self._show_add_dialog_with_dates(start, end)
            self.drag_start_date = None

    def _show_add_dialog(self):
        """Show the add plan dialog with today's date."""
        today = date.today()
        self._show_add_dialog_with_dates(today, today)

    def _show_add_dialog_with_dates(self, start: date, end: date):
        """Show the add plan dialog with specified dates."""
        dialog = AddPlanDialog(start, end, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_plan_data()
            if data["name"]:
                plan = Plan.create(
                    name=data["name"],
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                    plan_type=data["plan_type"],
                    color=data["color"]
                )
                self.plan_added.emit(plan)

    def _on_plan_clicked(self, plan_id: str):
        """Handle plan block click - show edit dialog."""
        plan = next((p for p in self.plans if p.id == plan_id), None)
        if plan:
            dialog = EditPlanDialog(plan, self)
            dialog.delete_requested.connect(lambda: self.plan_deleted.emit(plan_id))

            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_plan_data()
                if data["name"]:
                    self.plan_updated.emit(plan_id, data)

    def _on_plan_delete_requested(self, plan_id: str):
        """Handle plan delete request (right-click)."""
        self.plan_deleted.emit(plan_id)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.state = self.storage.load()

        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure the main window."""
        self.setWindowTitle("Monthly Plan Board")
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)

    def _setup_ui(self):
        """Set up the UI components."""
        self.calendar = MonthlyCalendar()
        self.calendar.set_plans(self.state.plans)
        self.calendar.plan_added.connect(self._on_plan_added)
        self.calendar.plan_updated.connect(self._on_plan_updated)
        self.calendar.plan_deleted.connect(self._on_plan_deleted)

        self.setCentralWidget(self.calendar)

    def _on_plan_added(self, plan: Plan):
        """Handle new plan addition."""
        self.state.add_plan(plan)
        self.storage.save(self.state)
        self.calendar.set_plans(self.state.plans)

    def _on_plan_updated(self, plan_id: str, data: dict):
        """Handle plan update."""
        self.state.update_plan(plan_id, **data)
        self.storage.save(self.state)
        self.calendar.set_plans(self.state.plans)

    def _on_plan_deleted(self, plan_id: str):
        """Handle plan deletion."""
        self.state.remove_plan(plan_id)
        self.storage.save(self.state)
        self.calendar.set_plans(self.state.plans)


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
