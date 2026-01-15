"""
Monthly Plan Board
개인용 월 단위 플랜 보드

12개월을 한눈에 보고 각 월에 플랜을 배치하는 보드.
플랜 블록이 주인공, 나머지는 배경.
"""
import sys
import os
from datetime import date
from calendar import monthrange

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFrame, QDialog, QLineEdit,
    QSizePolicy, QSpinBox, QCheckBox, QStackedWidget, QScrollArea
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
    """플랜 블록 - 컴팩트한 리스트 아이템."""

    clicked = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, plan: Plan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.04);
                border-left: 3px solid {self.plan.color};
                border-radius: 0px;
            }}
            QFrame:hover {{
                background-color: rgba(255, 255, 255, 0.08);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        # Plan name
        name_label = QLabel(self.plan.name)
        name_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 12px;
            font-weight: 500;
            background: transparent;
        """)
        layout.addWidget(name_label)

        layout.addStretch()

        # Date range (if exists)
        date_display = self.plan.get_date_display()
        if date_display:
            date_label = QLabel(date_display)
            date_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.3);
                font-size: 10px;
                background: transparent;
            """)
            layout.addWidget(date_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.plan.id)
        elif event.button() == Qt.RightButton:
            self.delete_requested.emit(self.plan.id)


class MonthZone(QFrame):
    """월 영역 - 배경 역할."""

    add_plan_clicked = Signal(int)
    plan_clicked = Signal(str)
    plan_delete_requested = Signal(str)
    month_clicked = Signal(int)

    def __init__(self, month: int, parent=None):
        super().__init__(parent)
        self.month = month
        self.plans: list[Plan] = []
        self._setup_ui()
        self.setCursor(Qt.PointingHandCursor)

    def _setup_ui(self):
        self.setObjectName("monthZone")
        self.setStyleSheet("""
            QFrame#monthZone {
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 10)
        layout.setSpacing(0)

        # Header - minimal, muted
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)

        month_label = QLabel(MONTH_NAMES[self.month])
        month_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.5);
        """)
        header_layout.addWidget(month_label)

        header_layout.addStretch()

        # Subtle add button
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(22, 22)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 11px;
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

        # Spacer between header and plans
        layout.addSpacing(12)

        # Plans container
        self.plans_widget = QWidget()
        self.plans_layout = QVBoxLayout(self.plans_widget)
        self.plans_layout.setContentsMargins(0, 0, 0, 0)
        self.plans_layout.setSpacing(6)

        layout.addWidget(self.plans_widget)
        layout.addStretch()

    def set_plans(self, plans: list[Plan]):
        self.plans = plans
        max_visible = 5

        while self.plans_layout.count():
            child = self.plans_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        visible_plans = plans[:max_visible]
        for plan in visible_plans:
            block = PlanBlock(plan)
            block.clicked.connect(self.plan_clicked.emit)
            block.delete_requested.connect(self.plan_delete_requested.emit)
            self.plans_layout.addWidget(block)

        # Show summary if more plans exist
        if len(plans) > max_visible:
            more_label = QLabel(f"+{len(plans) - max_visible}개 더보기")
            more_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.3);
                font-size: 11px;
                padding: 4px 0;
            """)
            more_label.setAlignment(Qt.AlignCenter)
            self.plans_layout.addWidget(more_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.month_clicked.emit(self.month)


class MonthDetailView(QWidget):
    """월 상세 보기 - 플랜 리스트."""

    back_clicked = Signal()
    plan_clicked = Signal(str)
    plan_delete_requested = Signal(str)
    add_plan_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.year = 0
        self.month = 0
        self.plans = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        self.back_btn = QPushButton("←")
        self.back_btn.setFixedSize(40, 40)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 20px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                color: white;
            }
        """)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(self.back_btn)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: rgba(255, 255, 255, 0.9);
            margin-left: 12px;
        """)
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.add_btn = QPushButton("+ 플랜 추가")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                color: rgba(255, 255, 255, 0.8);
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.add_btn.clicked.connect(lambda: self.add_plan_clicked.emit(self.month))
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Plans list area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.plans_container = QWidget()
        self.plans_layout = QVBoxLayout(self.plans_container)
        self.plans_layout.setContentsMargins(0, 8, 0, 8)
        self.plans_layout.setSpacing(4)
        self.plans_layout.addStretch()

        scroll.setWidget(self.plans_container)
        layout.addWidget(scroll, 1)

    def set_data(self, year: int, month: int, plans: list):
        self.year = year
        self.month = month
        self.plans = plans

        self.title_label.setText(f"{year}년 {MONTH_NAMES[month]}")

        # Clear existing plans
        while self.plans_layout.count() > 1:
            child = self.plans_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add plan items
        if not plans:
            empty_label = QLabel("플랜이 없습니다")
            empty_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.3);
                font-size: 15px;
                padding: 40px;
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            self.plans_layout.insertWidget(0, empty_label)
        else:
            for plan in plans:
                item = self._create_plan_item(plan)
                self.plans_layout.insertWidget(self.plans_layout.count() - 1, item)

    def _create_plan_item(self, plan: Plan) -> QFrame:
        item = QFrame()
        item.setFixedHeight(44)
        item.setCursor(Qt.PointingHandCursor)
        item.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.04);
                border-left: 3px solid {plan.color};
                border-radius: 0px;
            }}
            QFrame:hover {{
                background-color: rgba(255, 255, 255, 0.07);
            }}
        """)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(14, 0, 16, 0)
        layout.setSpacing(0)

        # Plan name
        name_label = QLabel(plan.name)
        name_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
            font-weight: 500;
            background: transparent;
        """)
        layout.addWidget(name_label)

        layout.addStretch()

        # Date range
        date_display = plan.get_date_display()
        if date_display:
            date_label = QLabel(date_display)
            date_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.3);
                font-size: 12px;
                background: transparent;
            """)
            layout.addWidget(date_label)

        # Make clickable
        item.mousePressEvent = lambda e, p=plan: self._on_item_click(e, p)

        return item

    def _on_item_click(self, event, plan: Plan):
        if event.button() == Qt.LeftButton:
            self.plan_clicked.emit(plan.id)
        elif event.button() == Qt.RightButton:
            self.plan_delete_requested.emit(plan.id)


class AddPlanDialog(QDialog):
    """플랜 추가 다이얼로그."""

    def __init__(self, year: int, month: int, parent=None):
        super().__init__(parent)
        self.year = year
        self.month = month
        self.max_day = monthrange(year, month)[1]
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("플랜 추가")
        self.setFixedSize(380, 280)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Title
        title = QLabel(f"{self.year}년 {MONTH_NAMES[self.month]}")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.5);
        """)
        layout.addWidget(title)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("플랜 이름")
        self.name_input.setMinimumHeight(44)
        self.name_input.setStyleSheet("""
            QLineEdit {
                font-size: 15px;
                padding: 0 16px;
                border-radius: 8px;
            }
        """)
        self.name_input.returnPressed.connect(self.accept)
        layout.addWidget(self.name_input)

        # Date range (optional)
        date_layout = QHBoxLayout()
        date_layout.setSpacing(12)

        self.date_checkbox = QCheckBox("기간 설정")
        self.date_checkbox.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 13px;")
        self.date_checkbox.toggled.connect(self._toggle_date_inputs)
        date_layout.addWidget(self.date_checkbox)

        self.start_day = QSpinBox()
        self.start_day.setRange(1, self.max_day)
        self.start_day.setValue(1)
        self.start_day.setMinimumHeight(40)
        self.start_day.setMinimumWidth(70)
        self.start_day.setSuffix("일")
        self.start_day.setEnabled(False)
        date_layout.addWidget(self.start_day)

        self.dash_label = QLabel("~")
        self.dash_label.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
        date_layout.addWidget(self.dash_label)

        self.end_day = QSpinBox()
        self.end_day.setRange(1, self.max_day)
        self.end_day.setValue(self.max_day)
        self.end_day.setMinimumHeight(40)
        self.end_day.setMinimumWidth(70)
        self.end_day.setSuffix("일")
        self.end_day.setEnabled(False)
        date_layout.addWidget(self.end_day)

        date_layout.addStretch()
        layout.addLayout(date_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("취소")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.15);
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
                background-color: rgba(255, 255, 255, 0.12);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.18);
            }
        """)
        add_btn.clicked.connect(self.accept)
        btn_layout.addWidget(add_btn)

        layout.addLayout(btn_layout)

    def _toggle_date_inputs(self, enabled: bool):
        self.start_day.setEnabled(enabled)
        self.end_day.setEnabled(enabled)
        if enabled:
            self.dash_label.setStyleSheet("color: rgba(255, 255, 255, 0.4);")
        else:
            self.dash_label.setStyleSheet("color: rgba(255, 255, 255, 0.2);")

    def get_plan_data(self, existing_count: int) -> dict:
        color = SIMPLE_COLORS[existing_count % len(SIMPLE_COLORS)]
        start_day = None
        end_day = None

        if self.date_checkbox.isChecked():
            start = self.start_day.value()
            end = self.end_day.value()
            # Ensure start <= end
            if start > end:
                start, end = end, start
            start_day = start
            end_day = end

        return {
            "name": self.name_input.text().strip(),
            "year": self.year,
            "month": self.month,
            "plan_type": PlanType.OTHER,
            "color": color,
            "start_day": start_day,
            "end_day": end_day
        }


class EditPlanDialog(QDialog):
    """플랜 수정 다이얼로그."""

    delete_requested = Signal()

    def __init__(self, plan: Plan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.max_day = monthrange(plan.year, plan.month)[1]
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("플랜 수정")
        self.setFixedSize(380, 320)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setText(self.plan.name)
        self.name_input.setMinimumHeight(44)
        self.name_input.setStyleSheet("""
            QLineEdit {
                font-size: 15px;
                padding: 0 16px;
                border-radius: 8px;
            }
        """)
        self.name_input.returnPressed.connect(self.accept)
        layout.addWidget(self.name_input)

        # Date range (optional)
        date_layout = QHBoxLayout()
        date_layout.setSpacing(12)

        has_date = self.plan.start_day is not None or self.plan.end_day is not None
        self.date_checkbox = QCheckBox("기간 설정")
        self.date_checkbox.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 13px;")
        self.date_checkbox.setChecked(has_date)
        self.date_checkbox.toggled.connect(self._toggle_date_inputs)
        date_layout.addWidget(self.date_checkbox)

        self.start_day = QSpinBox()
        self.start_day.setRange(1, self.max_day)
        self.start_day.setValue(self.plan.start_day or 1)
        self.start_day.setMinimumHeight(40)
        self.start_day.setMinimumWidth(70)
        self.start_day.setSuffix("일")
        self.start_day.setEnabled(has_date)
        date_layout.addWidget(self.start_day)

        self.dash_label = QLabel("~")
        self.dash_label.setStyleSheet(f"color: rgba(255, 255, 255, {0.4 if has_date else 0.2});")
        date_layout.addWidget(self.dash_label)

        self.end_day = QSpinBox()
        self.end_day.setRange(1, self.max_day)
        self.end_day.setValue(self.plan.end_day or self.max_day)
        self.end_day.setMinimumHeight(40)
        self.end_day.setMinimumWidth(70)
        self.end_day.setSuffix("일")
        self.end_day.setEnabled(has_date)
        date_layout.addWidget(self.end_day)

        date_layout.addStretch()
        layout.addLayout(date_layout)

        layout.addStretch()

        # Delete button
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
                border: 1px solid rgba(255, 255, 255, 0.15);
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
                background-color: rgba(255, 255, 255, 0.12);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.18);
            }
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _toggle_date_inputs(self, enabled: bool):
        self.start_day.setEnabled(enabled)
        self.end_day.setEnabled(enabled)
        if enabled:
            self.dash_label.setStyleSheet("color: rgba(255, 255, 255, 0.4);")
        else:
            self.dash_label.setStyleSheet("color: rgba(255, 255, 255, 0.2);")

    def _on_delete(self):
        self.delete_requested.emit()
        self.reject()

    def get_plan_data(self) -> dict:
        start_day = None
        end_day = None

        if self.date_checkbox.isChecked():
            start = self.start_day.value()
            end = self.end_day.value()
            if start > end:
                start, end = end, start
            start_day = start
            end_day = end

        return {
            "name": self.name_input.text().strip(),
            "start_day": start_day,
            "end_day": end_day
        }


class YearBoard(QWidget):
    """연간 보드 - 플랜이 주인공."""

    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.state = self.storage.load()
        self.month_zones: dict[int, MonthZone] = {}
        self.current_detail_month = None
        self._setup_ui()
        self._update_board()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stacked widget for view switching
        self.stack = QStackedWidget()

        # Grid view (12 months)
        self.grid_view = QWidget()
        self._setup_grid_view()
        self.stack.addWidget(self.grid_view)

        # Detail view (single month)
        self.detail_view = MonthDetailView()
        self.detail_view.back_clicked.connect(self._show_grid_view)
        self.detail_view.plan_clicked.connect(self._on_plan_clicked)
        self.detail_view.plan_delete_requested.connect(self._on_plan_delete)
        self.detail_view.add_plan_clicked.connect(self._on_add_plan)
        self.stack.addWidget(self.detail_view)

        layout.addWidget(self.stack)

    def _setup_grid_view(self):
        layout = QVBoxLayout(self.grid_view)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

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

        # Month grid
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        for month in range(1, 13):
            row = (month - 1) // 4
            col = (month - 1) % 4

            zone = MonthZone(month)
            zone.add_plan_clicked.connect(self._on_add_plan)
            zone.plan_clicked.connect(self._on_plan_clicked)
            zone.plan_delete_requested.connect(self._on_plan_delete)
            zone.month_clicked.connect(self._on_month_clicked)

            self.grid_layout.addWidget(zone, row, col)
            self.month_zones[month] = zone

        layout.addWidget(grid_widget, 1)

    def _update_board(self):
        self.year_label.setText(f"{self.state.current_year}")

        for month, zone in self.month_zones.items():
            plans = self.state.get_plans_for_month(self.state.current_year, month)
            zone.set_plans(plans)

    def _update_detail_view(self):
        if self.current_detail_month:
            plans = self.state.get_plans_for_month(self.state.current_year, self.current_detail_month)
            self.detail_view.set_data(self.state.current_year, self.current_detail_month, plans)

    def _show_grid_view(self):
        self.current_detail_month = None
        self._update_board()
        self.stack.setCurrentIndex(0)

    def _show_detail_view(self, month: int):
        self.current_detail_month = month
        plans = self.state.get_plans_for_month(self.state.current_year, month)
        self.detail_view.set_data(self.state.current_year, month, plans)
        self.stack.setCurrentIndex(1)

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
                    color=data["color"],
                    start_day=data["start_day"],
                    end_day=data["end_day"]
                )
                self.state.add_plan(plan)
                self.storage.save(self.state)
                self._update_board()
                self._update_detail_view()

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
                    self._update_detail_view()

    def _on_plan_delete(self, plan_id: str):
        self.state.remove_plan(plan_id)
        self.storage.save(self.state)
        self._update_board()
        self._update_detail_view()

    def _on_month_clicked(self, month: int):
        self._show_detail_view(month)


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

    # Clean dark theme
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
