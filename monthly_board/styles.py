"""
Dark theme styling for Monthly Plan Board.
"""

COLORS = {
    "bg_primary": "#0f0f1a",       # Main background (darker)
    "bg_secondary": "#1a1a2e",     # Card/cell background
    "bg_tertiary": "#252542",      # Hover states
    "bg_cell": "#16162a",          # Calendar cell
    "accent": "#4a9eff",           # Primary accent
    "accent_hover": "#6bb3ff",
    "text_primary": "#ffffff",
    "text_secondary": "#9090a0",
    "text_muted": "#505068",
    "border": "#2a2a4a",
    "today": "#3a3a5a",            # Today highlight
    "weekend": "#12121f",          # Weekend cell bg
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_primary']};
}}

QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
}}

QLabel {{
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QLabel#monthLabel {{
    font-size: 28px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

QLabel#yearLabel {{
    font-size: 16px;
    color: {COLORS['text_secondary']};
}}

QLabel#dayHeader {{
    font-size: 12px;
    font-weight: bold;
    color: {COLORS['text_muted']};
    padding: 8px;
}}

QLabel#dateNumber {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
}}

QLabel#dateNumberToday {{
    font-size: 13px;
    font-weight: bold;
    color: {COLORS['accent']};
}}

QPushButton {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    color: {COLORS['text_primary']};
}}

QPushButton:hover {{
    background-color: {COLORS['bg_tertiary']};
    border-color: {COLORS['accent']};
}}

QPushButton#navButton {{
    background-color: transparent;
    border: none;
    font-size: 20px;
    padding: 8px 16px;
    color: {COLORS['text_secondary']};
}}

QPushButton#navButton:hover {{
    color: {COLORS['text_primary']};
    background-color: {COLORS['bg_secondary']};
    border-radius: 8px;
}}

QPushButton#addButton {{
    background-color: {COLORS['accent']};
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    color: {COLORS['bg_primary']};
    font-weight: bold;
}}

QPushButton#addButton:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#deleteButton {{
    background-color: transparent;
    border: 1px solid #f87171;
    color: #f87171;
    border-radius: 6px;
    padding: 6px 12px;
}}

QPushButton#deleteButton:hover {{
    background-color: #f87171;
    color: {COLORS['bg_primary']};
}}

QFrame#calendarCell {{
    background-color: {COLORS['bg_cell']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
}}

QFrame#calendarCellToday {{
    background-color: {COLORS['today']};
    border: 1px solid {COLORS['accent']};
    border-radius: 4px;
}}

QFrame#calendarCellWeekend {{
    background-color: {COLORS['weekend']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
}}

QFrame#calendarCellOtherMonth {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid transparent;
    border-radius: 4px;
}}

QLineEdit {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    color: {COLORS['text_primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['accent']};
}}

QComboBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    color: {COLORS['text_primary']};
}}

QComboBox:hover {{
    border-color: {COLORS['accent']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 16px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent']};
    padding: 4px;
}}

QDateEdit {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    color: {COLORS['text_primary']};
}}

QDateEdit:focus {{
    border-color: {COLORS['accent']};
}}

QDateEdit::drop-down {{
    border: none;
    padding-right: 16px;
}}

QCalendarWidget {{
    background-color: {COLORS['bg_secondary']};
}}

QCalendarWidget QToolButton {{
    color: {COLORS['text_primary']};
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {COLORS['bg_tertiary']};
}}

QCalendarWidget QMenu {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
}}

QCalendarWidget QSpinBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    color: {COLORS['text_primary']};
}}

QCalendarWidget QAbstractItemView:enabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent']};
    selection-color: {COLORS['bg_primary']};
}}

QDialog {{
    background-color: {COLORS['bg_primary']};
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_primary']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""
