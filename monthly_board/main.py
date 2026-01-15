"""
Monthly Plan Board
개인용 월 단위 플랜 보드

12개월을 한눈에 보고 각 월에 플랜을 배치하는 보드.
플랜 블록이 주인공, 나머지는 배경.
"""
import sys
import os
from datetime import date

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFrame, QDialog, QLineEdit,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase

import qdarktheme

from models import Plan, PlanType, BoardState, PLAN_COLORS
from storage import Storage


MONTH_NAMES = ["", "1월", "2월", "3월", "4월", "5월", "6월",
               "7월", "8월", "9월", "10월", "11월", "12월"]

# Simplified color palette - just 4 muted colors
SIMPLE_COLORS = [
    "#5c6bc0",  # Indigo
    "#26a69a",  # Teal
    "#ef5350",  # Red
    "#ffa726",  # Orange
]


class PlanBlock(QFrame):
    """플랜 블록 - 화면의 주인공."""

    clicked = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, plan: Plan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(52)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.plan.color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {self._lighten_color(self.plan.color)};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)

        # Plan name only - no type label
        name_label = QLabel(self.plan.name)
        name_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
        """)
        layout.addWidget(name_label)
        layout.addStretch()

    def _lighten_color(self, hex_color: str) -> str:
        color = QColor(hex_color)
        h, s, l, a = color.getHslF()
        l = min(1.0, l + 0.08)
        color.setHslF(h, s, l, a)
        return color.name()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.plan.id)
        elif event.button() == Qt.RightButton:
            self.delete_requested.emit(self.plan.id)


class MonthZone(QWidget):
    """월 영역 - 배경 역할, 인터랙티브하지 않음."""

    add_plan_clicked = Signal(int)
    plan_clicked = Signal(str)
    plan_delete_requested = Signal(str)

    def __init__(self, month: int, parent=None):
        super().__init__(parent)
        self.month = month
        self.plans: list[Plan] = []
        self._setup_ui()

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 16)
        layout.setSpacing(8)

        # Header - minimal, muted
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)

        month_label = QLabel(MONTH_NAMES[self.month])
        month_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.4);
        """)
        header_layout.addWidget(month_label)

        header_layout.addStretch()

        # Subtle add button - only visible on intent
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(24, 24)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.25);
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.7);
            }
        """)
        self.add_btn.clicked.connect(lambda: self.add_plan_clicked.emit(self.month))
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Plans container - this is where the focus should be
        self.plans_widget = QWidget()
        self.plans_layout = QVBoxLayout(self.plans_widget)
        self.plans_layout.setContentsMargins(0, 4, 0, 0)
        self.plans_layout.setSpacing(10)

        layout.addWidget(self.plans_widget)
        layout.addStretch()

    def set_plans(self, plans: list[Plan]):
        self.plans = plans

        while self.plans_layout.count():
            child = self.plans_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for plan in plans:
            block = PlanBlock(plan)
            block.clicked.connect(self.plan_clicked.emit)
            block.delete_requested.connect(self.plan_delete_requested.emit)
            self.plans_layout.addWidget(block)


class AddPlanDialog(QDialog):
    """플랜 추가 다이얼로그 - 최소한의 입력."""

    def __init__(self, year: int, month: int, parent=None):
        super().__init__(parent)
        self.year = year
        self.month = month
        # Auto-assign color based on existing plans count
        self.color_index = 0
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("플랜 추가")
        self.setFixedSize(360, 200)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Title - simple
        title = QLabel(f"{MONTH_NAMES[self.month]}")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.5);
        """)
        layout.addWidget(title)

        # Name input only
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("플랜 이름")
        self.name_input.setMinimumHeight(48)
        self.name_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 0 16px;
            }
        """)
        layout.addWidget(self.name_input)

        layout.addStretch()

        # Buttons - minimal
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("취소")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.6);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        add_btn = QPushButton("추가")
        add_btn.setMinimumHeight(44)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        add_btn.clicked.connect(self.accept)
        btn_layout.addWidget(add_btn)

        layout.addLayout(btn_layout)

    def get_plan_data(self, existing_count: int) -> dict:
        # Auto-assign color based on how many plans exist
        color = SIMPLE_COLORS[existing_count % len(SIMPLE_COLORS)]
        return {
            "name": self.name_input.text().strip(),
            "year": self.year,
            "month": self.month,
            "plan_type": PlanType.OTHER,
            "color": color
        }


class EditPlanDialog(QDialog):
    """플랜 수정 다이얼로그."""

    delete_requested = Signal()

    def __init__(self, plan: Plan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("플랜 수정")
        self.setFixedSize(360, 240)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setText(self.plan.name)
        self.name_input.setMinimumHeight(48)
        self.name_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 0 16px;
            }
        """)
        layout.addWidget(self.name_input)

        layout.addStretch()

        # Delete button - subtle
        delete_btn = QPushButton("삭제")
        delete_btn.setMinimumHeight(40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: rgba(239, 83, 80, 0.7);
            }
            QPushButton:hover {
                color: #ef5350;
            }
        """)
        delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(delete_btn)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("취소")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.6);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("저장")
        save_btn.setMinimumHeight(44)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_delete(self):
        self.delete_requested.emit()
        self.reject()

    def get_plan_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
        }


class YearBoard(QWidget):
    """연간 보드 - 플랜이 주인공."""

    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.state = self.storage.load()
        self.month_zones: dict[int, MonthZone] = {}
        self._setup_ui()
        self._update_board()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(20)

        # Header - demoted, utility text
        header_layout = QHBoxLayout()

        # Navigation - small, subtle
        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(32, 32)
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
                color: rgba(255, 255, 255, 0.3);
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        prev_btn.clicked.connect(self._prev_year)
        header_layout.addWidget(prev_btn)

        # Year label - utility, not decorative
        self.year_label = QLabel()
        self.year_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.4);
        """)
        header_layout.addWidget(self.year_label)

        next_btn = QPushButton(">")
        next_btn.setFixedSize(32, 32)
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
                color: rgba(255, 255, 255, 0.3);
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        next_btn.clicked.connect(self._next_year)
        header_layout.addWidget(next_btn)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Month grid - passive scaffold
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        for month in range(1, 13):
            row = (month - 1) // 4
            col = (month - 1) % 4

            zone = MonthZone(month)
            zone.add_plan_clicked.connect(self._on_add_plan)
            zone.plan_clicked.connect(self._on_plan_clicked)
            zone.plan_delete_requested.connect(self._on_plan_delete)

            self.grid_layout.addWidget(zone, row, col)
            self.month_zones[month] = zone

        layout.addWidget(grid_widget, 1)

    def _update_board(self):
        self.year_label.setText(f"{self.state.current_year}")

        for month, zone in self.month_zones.items():
            plans = self.state.get_plans_for_month(self.state.current_year, month)
            zone.set_plans(plans)

    def _prev_year(self):
        self.state.current_year -= 1
        self.storage.save(self.state)
        self._update_board()

    def _next_year(self):
        self.state.current_year += 1
        self.storage.save(self.state)
        self._update_board()

    def _on_add_plan(self, month: int):
        dialog = AddPlanDialog(self.state.current_year, month, self)
        if dialog.exec() == QDialog.Accepted:
            existing = self.state.get_plans_for_month(self.state.current_year, month)
            data = dialog.get_plan_data(len(existing))
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
        self.state.remove_plan(plan_id)
        self.storage.save(self.state)
        self._update_board()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        self.setWindowTitle("Monthly Plan Board")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

    def _setup_ui(self):
        self.board = YearBoard()
        self.setCentralWidget(self.board)


def load_fonts():
    """Load Pretendard fonts for better Korean readability."""
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")

    font_files = [
        "Pretendard-Regular.otf",
        "Pretendard-Medium.otf",
        "Pretendard-SemiBold.otf",
        "Pretendard-Bold.otf",
    ]

    for font_file in font_files:
        font_path = os.path.join(fonts_dir, font_file)
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)


def main():
    app = QApplication(sys.argv)

    # Load custom fonts first
    load_fonts()

    # Clean dark theme with better readability
    app.setStyleSheet(qdarktheme.load_stylesheet("dark"))

    # Use Pretendard for better Korean readability
    font = QFont("Pretendard", 11)
    font.setWeight(QFont.Weight.Normal)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
