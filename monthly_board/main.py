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
    QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from qt_material import apply_stylesheet, list_themes

from models import Plan, PlanType, BoardState, PLAN_COLORS
from storage import Storage


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
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.plan.color};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: {self._lighten_color(self.plan.color)};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        # Plan name
        name_label = QLabel(self.plan.name)
        name_label.setStyleSheet("""
            color: white;
            font-size: 13px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(name_label)

        layout.addStretch()

        # Type badge
        type_label = QLabel(self.plan.plan_type.label)
        type_label.setStyleSheet("""
            color: rgba(255,255,255,0.75);
            font-size: 11px;
            background: transparent;
        """)
        layout.addWidget(type_label)

    def _lighten_color(self, hex_color: str) -> str:
        """Lighten a hex color."""
        color = QColor(hex_color)
        h, s, l, a = color.getHslF()
        l = min(1.0, l + 0.12)
        color.setHslF(h, s, l, a)
        return color.name()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.plan.id)
        elif event.button() == Qt.RightButton:
            self.delete_requested.emit(self.plan.id)


class MonthCard(QFrame):
    """A card representing a single month with its plans."""

    add_plan_clicked = Signal(int)
    plan_clicked = Signal(str)
    plan_delete_requested = Signal(str)

    def __init__(self, month: int, is_current: bool, accent_color: str, parent=None):
        super().__init__(parent)
        self.month = month
        self.is_current = is_current
        self.accent_color = accent_color
        self.plans: list[Plan] = []
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("monthCard")
        if self.is_current:
            self.setStyleSheet(f"""
                QFrame#monthCard {{
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 2px solid {self.accent_color};
                    border-radius: 16px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame#monthCard {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                }
                QFrame#monthCard:hover {
                    background-color: rgba(255, 255, 255, 0.08);
                }
            """)

        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        self.month_label = QLabel(MONTH_NAMES[self.month])
        if self.is_current:
            self.month_label.setStyleSheet(f"""
                font-size: 20px;
                font-weight: bold;
                color: {self.accent_color};
            """)
        else:
            self.month_label.setStyleSheet("""
                font-size: 20px;
                font-weight: bold;
                color: white;
            """)
        header_layout.addWidget(self.month_label)

        header_layout.addStretch()

        # Add button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.accent_color};
                border-color: {self.accent_color};
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

        while self.plans_layout.count():
            child = self.plans_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for plan in plans:
            card = PlanCard(plan)
            card.clicked.connect(self.plan_clicked.emit)
            card.delete_requested.connect(self.plan_delete_requested.emit)
            self.plans_layout.addWidget(card)

    def update_current_state(self, is_current: bool, accent_color: str):
        """Update the current month highlight."""
        self.is_current = is_current
        self.accent_color = accent_color

        if is_current:
            self.setStyleSheet(f"""
                QFrame#monthCard {{
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 2px solid {accent_color};
                    border-radius: 16px;
                }}
            """)
            self.month_label.setStyleSheet(f"""
                font-size: 20px;
                font-weight: bold;
                color: {accent_color};
            """)
        else:
            self.setStyleSheet("""
                QFrame#monthCard {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                }
                QFrame#monthCard:hover {
                    background-color: rgba(255, 255, 255, 0.08);
                }
            """)
            self.month_label.setStyleSheet("""
                font-size: 20px;
                font-weight: bold;
                color: white;
            """)


class AddPlanDialog(QDialog):
    """Dialog for adding a new plan to a month."""

    def __init__(self, year: int, month: int, accent_color: str, parent=None):
        super().__init__(parent)
        self.year = year
        self.month = month
        self.accent_color = accent_color
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
        title = QLabel(f"{self.year}년 {MONTH_NAMES[self.month]} 플랜")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Name input
        name_label = QLabel("플랜 이름")
        name_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.7);")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("플랜 이름을 입력하세요")
        self.name_input.setMinimumHeight(44)
        layout.addWidget(self.name_input)

        # Type selection
        type_label = QLabel("타입")
        type_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.7);")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(44)
        for plan_type in PlanType:
            self.type_combo.addItem(plan_type.label, plan_type)
        layout.addWidget(self.type_combo)

        # Color selection
        color_label = QLabel("색상")
        color_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.7);")
        layout.addWidget(color_label)

        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(10)
        self.color_buttons = []

        for color in PLAN_COLORS:
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 3px solid transparent;
                    border-radius: 16px;
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
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.add_btn = QPushButton("추가")
        self.add_btn.setMinimumHeight(44)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color};
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(self.accent_color)};
            }}
        """)
        self.add_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

    def _lighten_color(self, hex_color: str) -> str:
        color = QColor(hex_color)
        h, s, l, a = color.getHslF()
        l = min(1.0, l + 0.1)
        color.setHslF(h, s, l, a)
        return color.name()

    def _select_color(self, color: str, button: QPushButton):
        """Select a color."""
        self.selected_color = color

        for btn in self.color_buttons:
            c = btn.styleSheet().split("background-color: ")[1].split(";")[0]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c};
                    border: 3px solid transparent;
                    border-radius: 16px;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 3px solid white;
                border-radius: 16px;
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

    def __init__(self, plan: Plan, accent_color: str, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.accent_color = accent_color
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
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Name input
        name_label = QLabel("플랜 이름")
        name_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.7);")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setText(self.plan.name)
        self.name_input.setMinimumHeight(44)
        layout.addWidget(self.name_input)

        # Type selection
        type_label = QLabel("타입")
        type_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.7);")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(44)
        for plan_type in PlanType:
            self.type_combo.addItem(plan_type.label, plan_type)
            if plan_type == self.plan.plan_type:
                self.type_combo.setCurrentIndex(self.type_combo.count() - 1)
        layout.addWidget(self.type_combo)

        # Color selection
        color_label = QLabel("색상")
        color_label.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.7);")
        layout.addWidget(color_label)

        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(10)
        self.color_buttons = []

        for color in PLAN_COLORS:
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.PointingHandCursor)
            is_selected = color == self.plan.color
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 3px solid {"white" if is_selected else "transparent"};
                    border-radius: 16px;
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
        delete_btn.setMinimumHeight(40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #f44336;
                border-radius: 8px;
                color: #f44336;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
                color: white;
            }
        """)
        delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(delete_btn)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("취소")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("저장")
        save_btn.setMinimumHeight(44)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color};
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(self.accent_color)};
            }}
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _lighten_color(self, hex_color: str) -> str:
        color = QColor(hex_color)
        h, s, l, a = color.getHslF()
        l = min(1.0, l + 0.1)
        color.setHslF(h, s, l, a)
        return color.name()

    def _select_color(self, color: str, button: QPushButton):
        """Select a color."""
        self.selected_color = color

        for btn in self.color_buttons:
            c = btn.styleSheet().split("background-color: ")[1].split(";")[0]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c};
                    border: 3px solid transparent;
                    border-radius: 16px;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 3px solid white;
                border-radius: 16px;
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

    def __init__(self, accent_color: str):
        super().__init__()
        self.accent_color = accent_color
        self.storage = Storage()
        self.state = self.storage.load()
        self.month_cards: dict[int, MonthCard] = {}
        self._setup_ui()
        self._update_board()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 40)
        layout.setSpacing(28)

        # Header
        header_layout = QHBoxLayout()

        # Navigation - Previous
        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(48, 48)
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 24px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.accent_color};
                border-color: {self.accent_color};
                color: white;
            }}
        """)
        prev_btn.clicked.connect(self._prev_year)
        header_layout.addWidget(prev_btn)

        header_layout.addStretch()

        # Year display
        self.year_label = QLabel()
        self.year_label.setStyleSheet(f"""
            font-size: 36px;
            font-weight: bold;
            color: {self.accent_color};
        """)
        header_layout.addWidget(self.year_label)

        header_layout.addStretch()

        # Navigation - Next
        next_btn = QPushButton(">")
        next_btn.setFixedSize(48, 48)
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 24px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.accent_color};
                border-color: {self.accent_color};
                color: white;
            }}
        """)
        next_btn.clicked.connect(self._next_year)
        header_layout.addWidget(next_btn)

        layout.addLayout(header_layout)

        # Month grid (4 columns x 3 rows)
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        current_month = date.today().month
        current_year = date.today().year

        for month in range(1, 13):
            row = (month - 1) // 4
            col = (month - 1) % 4

            is_current = (self.state.current_year == current_year and month == current_month)
            card = MonthCard(month, is_current, self.accent_color)
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

            is_current = (self.state.current_year == current_year and month == current_month)
            card.update_current_state(is_current, self.accent_color)

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
        dialog = AddPlanDialog(self.state.current_year, month, self.accent_color, self)
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
            dialog = EditPlanDialog(plan, self.accent_color, self)
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

    def __init__(self, accent_color: str):
        super().__init__()
        self.accent_color = accent_color
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure the main window."""
        self.setWindowTitle("Monthly Plan Board")
        self.setMinimumSize(1100, 750)
        self.resize(1300, 850)

    def _setup_ui(self):
        """Set up the UI components."""
        self.board = YearBoard(self.accent_color)
        self.setCentralWidget(self.board)


def main():
    """Application entry point."""
    app = QApplication(sys.argv)

    # Apply Material Design theme
    # Available themes: dark_teal, dark_cyan, dark_amber, dark_pink, etc.
    apply_stylesheet(app, theme='dark_teal.xml')

    # Get accent color from theme
    accent_color = "#009688"  # Teal

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow(accent_color)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
