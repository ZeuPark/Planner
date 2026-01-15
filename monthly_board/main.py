"""
Monthly Plan Board
개인용 월 단위 플랜 보드

12개월을 한눈에 보고 각 월에 플랜을 추가하는 보드.
"""
import sys
from datetime import date

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFrame, QDialog, QLineEdit,
    QComboBox, QSizePolicy, QSpacerItem, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QBrush

from models import Plan, PlanType, BoardState, PLAN_COLORS
from storage import Storage
from styles import STYLESHEET, COLORS


MONTH_NAMES = ["", "1월", "2월", "3월", "4월", "5월", "6월",
               "7월", "8월", "9월", "10월", "11월", "12월"]


class PlanCard(QFrame):
    """A card representing a single plan."""

    clicked = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, plan: Plan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.plan.color};
                border-radius: 8px;
                padding: 0px;
            }}
            QFrame:hover {{
                background-color: {self._lighten_color(self.plan.color)};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Plan name
        name_label = QLabel(self.plan.name)
        name_label.setStyleSheet(f"""
            color: white;
            font-size: 13px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(name_label)

        layout.addStretch()

        # Type badge
        type_label = QLabel(self.plan.plan_type.label)
        type_label.setStyleSheet(f"""
            color: rgba(255,255,255,0.7);
            font-size: 11px;
            background: transparent;
        """)
        layout.addWidget(type_label)

    def _lighten_color(self, hex_color: str) -> str:
        """Lighten a hex color."""
        color = QColor(hex_color)
        h, s, l, a = color.getHslF()
        l = min(1.0, l + 0.1)
        color.setHslF(h, s, l, a)
        return color.name()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.plan.id)
        elif event.button() == Qt.RightButton:
            self.delete_requested.emit(self.plan.id)


class MonthCard(QFrame):
    """A card representing a single month with its plans."""

    add_plan_clicked = Signal(int)  # month number
    plan_clicked = Signal(str)  # plan id
    plan_delete_requested = Signal(str)  # plan id

    def __init__(self, month: int, is_current: bool, parent=None):
        super().__init__(parent)
        self.month = month
        self.is_current = is_current
        self.plans: list[Plan] = []
        self._setup_ui()

    def _setup_ui(self):
        if self.is_current:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_secondary']};
                    border: 2px solid {COLORS['accent']};
                    border-radius: 16px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 16px;
                }}
            """)

        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        month_label = QLabel(MONTH_NAMES[self.month])
        if self.is_current:
            month_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {COLORS['accent']};
            """)
        else:
            month_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {COLORS['text_primary']};
            """)
        header_layout.addWidget(month_label)

        header_layout.addStretch()

        # Add button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                color: {COLORS['text_secondary']};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
                border-color: {COLORS['accent']};
                color: white;
            }}
        """)
        add_btn.clicked.connect(lambda: self.add_plan_clicked.emit(self.month))
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Plans container
        self.plans_widget = QWidget()
        self.plans_layout = QVBoxLayout(self.plans_widget)
        self.plans_layout.setContentsMargins(0, 0, 0, 0)
        self.plans_layout.setSpacing(8)

        layout.addWidget(self.plans_widget)
        layout.addStretch()

    def set_plans(self, plans: list[Plan]):
        """Set the plans to display in this month."""
        self.plans = plans

        # Clear existing
        while self.plans_layout.count():
            child = self.plans_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add plan cards
        for plan in plans:
            card = PlanCard(plan)
            card.clicked.connect(self.plan_clicked.emit)
            card.delete_requested.connect(self.plan_delete_requested.emit)
            self.plans_layout.addWidget(card)


class AddPlanDialog(QDialog):
    """Dialog for adding a new plan to a month."""

    def __init__(self, year: int, month: int, parent=None):
        super().__init__(parent)
        self.year = year
        self.month = month
        self.selected_color = PLAN_COLORS[0]
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("플랜 추가")
        self.setFixedSize(380, 340)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Title
        title = QLabel(f"{self.year}년 {MONTH_NAMES[self.month]} 플랜")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Name input
        name_label = QLabel("플랜 이름")
        name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("플랜 이름을 입력하세요")
        layout.addWidget(self.name_input)

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

        for color in PLAN_COLORS:
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
        """Select a color."""
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

    def get_plan_data(self) -> dict:
        """Get the plan data from the dialog."""
        return {
            "name": self.name_input.text().strip(),
            "year": self.year,
            "month": self.month,
            "plan_type": self.type_combo.currentData(),
            "color": self.selected_color
        }


class EditPlanDialog(QDialog):
    """Dialog for editing a plan."""

    delete_requested = Signal()

    def __init__(self, plan: Plan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.selected_color = plan.color
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("플랜 수정")
        self.setFixedSize(380, 380)
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
        """Select a color."""
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
        """Handle delete."""
        self.delete_requested.emit()
        self.reject()

    def get_plan_data(self) -> dict:
        """Get the updated plan data."""
        return {
            "name": self.name_input.text().strip(),
            "plan_type": self.type_combo.currentData(),
            "color": self.selected_color
        }


class YearBoard(QWidget):
    """The main 12-month board widget."""

    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.state = self.storage.load()
        self.month_cards: dict[int, MonthCard] = {}
        self._setup_ui()
        self._update_board()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(24)

        # Header
        header_layout = QHBoxLayout()

        # Navigation
        prev_btn = QPushButton("<")
        prev_btn.setObjectName("navButton")
        prev_btn.clicked.connect(self._prev_year)
        prev_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(prev_btn)

        header_layout.addStretch()

        # Year display
        self.year_label = QLabel()
        self.year_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        header_layout.addWidget(self.year_label)

        header_layout.addStretch()

        next_btn = QPushButton(">")
        next_btn.setObjectName("navButton")
        next_btn.clicked.connect(self._next_year)
        next_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(next_btn)

        layout.addLayout(header_layout)

        # Month grid (4 columns x 3 rows)
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        current_month = date.today().month
        current_year = date.today().year

        for month in range(1, 13):
            row = (month - 1) // 4
            col = (month - 1) % 4

            is_current = (self.state.current_year == current_year and month == current_month)
            card = MonthCard(month, is_current)
            card.add_plan_clicked.connect(self._on_add_plan)
            card.plan_clicked.connect(self._on_plan_clicked)
            card.plan_delete_requested.connect(self._on_plan_delete)

            self.grid_layout.addWidget(card, row, col)
            self.month_cards[month] = card

        layout.addWidget(grid_widget, 1)

    def _update_board(self):
        """Update the board display."""
        self.year_label.setText(f"{self.state.current_year}년")

        current_month = date.today().month
        current_year = date.today().year

        for month, card in self.month_cards.items():
            plans = self.state.get_plans_for_month(self.state.current_year, month)
            card.set_plans(plans)

            # Update current month highlight
            is_current = (self.state.current_year == current_year and month == current_month)
            if is_current:
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS['bg_secondary']};
                        border: 2px solid {COLORS['accent']};
                        border-radius: 16px;
                    }}
                """)
            else:
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS['bg_secondary']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 16px;
                    }}
                """)

    def _prev_year(self):
        """Go to previous year."""
        self.state.current_year -= 1
        self.storage.save(self.state)
        self._update_board()

    def _next_year(self):
        """Go to next year."""
        self.state.current_year += 1
        self.storage.save(self.state)
        self._update_board()

    def _on_add_plan(self, month: int):
        """Handle add plan button click."""
        dialog = AddPlanDialog(self.state.current_year, month, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_plan_data()
            if data["name"]:
                plan = Plan.create(
                    name=data["name"],
                    year=data["year"],
                    month=data["month"],
                    plan_type=data["plan_type"],
                    color=data["color"]
                )
                self.state.add_plan(plan)
                self.storage.save(self.state)
                self._update_board()

    def _on_plan_clicked(self, plan_id: str):
        """Handle plan click - show edit dialog."""
        plan = self.state.get_plan(plan_id)
        if plan:
            dialog = EditPlanDialog(plan, self)
            dialog.delete_requested.connect(lambda: self._on_plan_delete(plan_id))

            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_plan_data()
                if data["name"]:
                    self.state.update_plan(plan_id, **data)
                    self.storage.save(self.state)
                    self._update_board()

    def _on_plan_delete(self, plan_id: str):
        """Handle plan deletion."""
        self.state.remove_plan(plan_id)
        self.storage.save(self.state)
        self._update_board()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure the main window."""
        self.setWindowTitle("Monthly Plan Board")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

    def _setup_ui(self):
        """Set up the UI components."""
        self.board = YearBoard()
        self.setCentralWidget(self.board)


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
