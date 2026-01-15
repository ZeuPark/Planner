"""
Dark theme styling for Long Plan Desktop App.
"""

# Color palette - minimal 2-color approach
COLORS = {
    "bg_primary": "#1a1a2e",      # Main background
    "bg_secondary": "#16213e",     # Card background
    "bg_tertiary": "#0f0f1a",      # Darker elements
    "accent": "#4a9eff",           # Primary accent (blue)
    "accent_hover": "#6bb3ff",     # Accent hover state
    "text_primary": "#ffffff",     # Main text
    "text_secondary": "#a0a0a0",   # Muted text
    "text_muted": "#606080",       # Very muted text
    "success": "#4ade80",          # Complete button
    "success_hover": "#6ee7a0",
    "warning": "#fbbf24",          # Skip button
    "warning_hover": "#fcd34d",
    "border": "#2a2a4a",           # Subtle borders
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

QLabel#goalLabel {{
    color: {COLORS['text_secondary']};
    font-size: 14px;
}}

QLabel#phaseLabel {{
    color: {COLORS['accent']};
    font-size: 16px;
    font-weight: bold;
}}

QLabel#currentItemLabel {{
    color: {COLORS['text_primary']};
    font-size: 28px;
    font-weight: bold;
}}

QLabel#progressLabel {{
    color: {COLORS['text_muted']};
    font-size: 13px;
}}

QLabel#titleLabel {{
    color: {COLORS['text_primary']};
    font-size: 24px;
    font-weight: bold;
}}

QLabel#subtitleLabel {{
    color: {COLORS['text_secondary']};
    font-size: 14px;
}}

QLineEdit {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px 20px;
    font-size: 16px;
    color: {COLORS['text_primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['accent']};
}}

QLineEdit::placeholder {{
    color: {COLORS['text_muted']};
}}

QComboBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px 20px;
    font-size: 16px;
    color: {COLORS['text_primary']};
    min-width: 150px;
}}

QComboBox:hover {{
    border-color: {COLORS['accent']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    selection-background-color: {COLORS['accent']};
    padding: 8px;
}}

QSpinBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px 20px;
    font-size: 16px;
    color: {COLORS['text_primary']};
}}

QSpinBox:focus {{
    border-color: {COLORS['accent']};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: transparent;
    border: none;
    width: 20px;
}}

QPushButton {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px 32px;
    font-size: 15px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

QPushButton:hover {{
    background-color: {COLORS['bg_tertiary']};
    border-color: {COLORS['accent']};
}}

QPushButton#completeBtn {{
    background-color: {COLORS['success']};
    border: none;
    color: {COLORS['bg_primary']};
}}

QPushButton#completeBtn:hover {{
    background-color: {COLORS['success_hover']};
}}

QPushButton#skipBtn {{
    background-color: transparent;
    border: 1px solid {COLORS['warning']};
    color: {COLORS['warning']};
}}

QPushButton#skipBtn:hover {{
    background-color: {COLORS['warning']};
    color: {COLORS['bg_primary']};
}}

QPushButton#regenerateBtn {{
    background-color: transparent;
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_secondary']};
    padding: 12px 24px;
    font-size: 13px;
}}

QPushButton#regenerateBtn:hover {{
    border-color: {COLORS['text_secondary']};
    color: {COLORS['text_primary']};
}}

QPushButton#primaryBtn {{
    background-color: {COLORS['accent']};
    border: none;
    color: {COLORS['bg_primary']};
    padding: 18px 48px;
    font-size: 16px;
}}

QPushButton#primaryBtn:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#primaryBtn:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}

QFrame#card {{
    background-color: {COLORS['bg_secondary']};
    border-radius: 20px;
    border: 1px solid {COLORS['border']};
}}

QFrame#focusCard {{
    background-color: {COLORS['bg_secondary']};
    border-radius: 24px;
    border: none;
}}

QProgressBar {{
    background-color: {COLORS['bg_tertiary']};
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 4px;
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
