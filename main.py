"""
Long Plan Desktop App
개인용 장기 플랜 생성기

A personal long-term planning app that eliminates decision fatigue.
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton, QFrame,
    QProgressBar, QStackedWidget, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from models import Plan, Duration, ItemStatus
from storage import Storage
from plan_generator import PlanGenerator
from styles import STYLESHEET


class InputView(QWidget):
    """View for creating a new plan."""

    plan_created = Signal(Plan)

    def __init__(self):
        super().__init__()
        self.generator = PlanGenerator()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(0)

        # Top spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Title
        title = QLabel("새로운 플랜")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(12)

        # Subtitle
        subtitle = QLabel("한 번 결정하고, 고민 없이 따라가세요")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(60)

        # Form container
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(24)

        # Goal input
        goal_label = QLabel("목표")
        goal_label.setObjectName("goalLabel")
        form_layout.addWidget(goal_label)

        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("이루고 싶은 목표를 한 줄로 작성하세요")
        self.goal_input.textChanged.connect(self._validate_form)
        form_layout.addWidget(self.goal_input)

        form_layout.addSpacing(16)

        # Duration and hours row
        row_layout = QHBoxLayout()
        row_layout.setSpacing(24)

        # Duration
        duration_container = QVBoxLayout()
        duration_label = QLabel("전체 기간")
        duration_label.setObjectName("goalLabel")
        duration_container.addWidget(duration_label)

        self.duration_combo = QComboBox()
        for duration in Duration:
            self.duration_combo.addItem(duration.label, duration)
        duration_container.addWidget(self.duration_combo)
        row_layout.addLayout(duration_container)

        # Weekly hours
        hours_container = QVBoxLayout()
        hours_label = QLabel("주당 투자 시간")
        hours_label.setObjectName("goalLabel")
        hours_container.addWidget(hours_label)

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(1, 40)
        self.hours_spin.setValue(5)
        self.hours_spin.setSuffix(" 시간")
        hours_container.addWidget(self.hours_spin)
        row_layout.addLayout(hours_container)

        form_layout.addLayout(row_layout)

        # Center form
        form_wrapper = QHBoxLayout()
        form_wrapper.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        form_wrapper.addWidget(form_container)
        form_wrapper.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(form_wrapper)

        # Set form width
        form_container.setFixedWidth(400)

        layout.addSpacing(48)

        # Create button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.create_btn = QPushButton("플랜 생성하기")
        self.create_btn.setObjectName("primaryBtn")
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self._create_plan)
        self.create_btn.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(self.create_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Bottom spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def _validate_form(self):
        """Enable create button only when goal is entered."""
        is_valid = len(self.goal_input.text().strip()) > 0
        self.create_btn.setEnabled(is_valid)

    def _create_plan(self):
        """Generate and emit the new plan."""
        goal = self.goal_input.text().strip()
        duration = self.duration_combo.currentData()
        weekly_hours = self.hours_spin.value()

        plan = self.generator.generate(goal, duration, weekly_hours)
        self.plan_created.emit(plan)

    def reset(self):
        """Reset the form."""
        self.goal_input.clear()
        self.duration_combo.setCurrentIndex(0)
        self.hours_spin.setValue(5)


class FocusView(QWidget):
    """View showing the current task focus."""

    complete_clicked = Signal()
    skip_clicked = Signal()
    regenerate_clicked = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(0)

        # Top section with goal
        self.goal_label = QLabel()
        self.goal_label.setObjectName("goalLabel")
        self.goal_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.goal_label)

        layout.addSpacing(8)

        # Progress bar
        progress_container = QHBoxLayout()
        progress_container.addStretch()

        progress_widget = QWidget()
        progress_widget.setFixedWidth(300)
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setObjectName("progressLabel")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        progress_container.addWidget(progress_widget)
        progress_container.addStretch()
        layout.addLayout(progress_container)

        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Focus card
        self.focus_card = QFrame()
        self.focus_card.setObjectName("focusCard")
        self.focus_card.setFixedSize(500, 280)

        card_layout = QVBoxLayout(self.focus_card)
        card_layout.setContentsMargins(48, 48, 48, 48)
        card_layout.setSpacing(16)

        # Phase label
        self.phase_label = QLabel()
        self.phase_label.setObjectName("phaseLabel")
        self.phase_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.phase_label)

        card_layout.addStretch()

        # Current item
        self.item_label = QLabel()
        self.item_label.setObjectName("currentItemLabel")
        self.item_label.setAlignment(Qt.AlignCenter)
        self.item_label.setWordWrap(True)
        card_layout.addWidget(self.item_label)

        card_layout.addStretch()

        # Center the card
        card_container = QHBoxLayout()
        card_container.addStretch()
        card_container.addWidget(self.focus_card)
        card_container.addStretch()
        layout.addLayout(card_container)

        # Spacer
        layout.addSpacing(48)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.addStretch()

        self.skip_btn = QPushButton("나중에")
        self.skip_btn.setObjectName("skipBtn")
        self.skip_btn.clicked.connect(self.skip_clicked.emit)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(self.skip_btn)

        self.complete_btn = QPushButton("완료")
        self.complete_btn.setObjectName("completeBtn")
        self.complete_btn.clicked.connect(self.complete_clicked.emit)
        self.complete_btn.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(self.complete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Bottom spacer
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Regenerate button at bottom
        regen_layout = QHBoxLayout()
        regen_layout.addStretch()

        self.regenerate_btn = QPushButton("플랜 다시 만들기")
        self.regenerate_btn.setObjectName("regenerateBtn")
        self.regenerate_btn.clicked.connect(self.regenerate_clicked.emit)
        self.regenerate_btn.setCursor(Qt.PointingHandCursor)
        regen_layout.addWidget(self.regenerate_btn)

        regen_layout.addStretch()
        layout.addLayout(regen_layout)

    def update_view(self, plan: Plan):
        """Update the view with plan data."""
        self.goal_label.setText(plan.goal)

        completed, total = plan.get_progress()
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(completed)
        self.progress_label.setText(f"{completed} / {total}")

        current_item = plan.get_current_item()
        current_phase = plan.get_current_phase()

        if current_item and current_phase:
            self.phase_label.setText(current_phase.name)
            self.item_label.setText(current_item.name)
            self.complete_btn.setEnabled(True)
            self.skip_btn.setEnabled(True)
        else:
            self.phase_label.setText("완료!")
            self.item_label.setText("모든 항목을 완료했습니다")
            self.complete_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)


class CompletedView(QWidget):
    """View shown when all items are completed."""

    regenerate_clicked = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)

        layout.addStretch()

        # Celebration message
        title = QLabel("축하합니다!")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px;")
        layout.addWidget(title)

        layout.addSpacing(16)

        subtitle = QLabel("모든 플랜을 완료했습니다")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(48)

        # New plan button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        new_plan_btn = QPushButton("새 플랜 시작하기")
        new_plan_btn.setObjectName("primaryBtn")
        new_plan_btn.clicked.connect(self.regenerate_clicked.emit)
        new_plan_btn.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(new_plan_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def update_view(self, plan: Plan):
        """Update with the completed plan info."""
        pass  # Could show stats here if needed


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.current_plan = None

        self._setup_window()
        self._setup_ui()
        self._load_plan()

    def _setup_window(self):
        """Configure the main window."""
        self.setWindowTitle("Long Plan")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)

    def _setup_ui(self):
        """Set up the UI components."""
        # Central widget with stacked views
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Input view
        self.input_view = InputView()
        self.input_view.plan_created.connect(self._on_plan_created)
        self.stack.addWidget(self.input_view)

        # Focus view
        self.focus_view = FocusView()
        self.focus_view.complete_clicked.connect(self._on_complete)
        self.focus_view.skip_clicked.connect(self._on_skip)
        self.focus_view.regenerate_clicked.connect(self._on_regenerate)
        self.stack.addWidget(self.focus_view)

        # Completed view
        self.completed_view = CompletedView()
        self.completed_view.regenerate_clicked.connect(self._on_regenerate)
        self.stack.addWidget(self.completed_view)

    def _load_plan(self):
        """Load existing plan or show input view."""
        self.current_plan = self.storage.load()

        if self.current_plan:
            self._show_appropriate_view()
        else:
            self.stack.setCurrentWidget(self.input_view)

    def _show_appropriate_view(self):
        """Show the appropriate view based on plan state."""
        if not self.current_plan:
            self.stack.setCurrentWidget(self.input_view)
            return

        current_item = self.current_plan.get_current_item()

        if current_item:
            self.focus_view.update_view(self.current_plan)
            self.stack.setCurrentWidget(self.focus_view)
        else:
            self.completed_view.update_view(self.current_plan)
            self.stack.setCurrentWidget(self.completed_view)

    def _on_plan_created(self, plan: Plan):
        """Handle new plan creation."""
        self.current_plan = plan
        self.storage.save(plan)
        self._show_appropriate_view()

    def _on_complete(self):
        """Handle complete button click."""
        if self.current_plan:
            self.current_plan.complete_current()
            self.storage.save(self.current_plan)
            self._show_appropriate_view()

    def _on_skip(self):
        """Handle skip button click."""
        if self.current_plan:
            self.current_plan.skip_current()
            self.storage.save(self.current_plan)
            self._show_appropriate_view()

    def _on_regenerate(self):
        """Handle regenerate/new plan request."""
        self.current_plan = None
        self.storage.clear()
        self.input_view.reset()
        self.stack.setCurrentWidget(self.input_view)


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
