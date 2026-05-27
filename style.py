light_theme = """
QWidget {
    background: #f3f4f6;
    color: #1f2937;
    font-family: Segoe UI, Arial, sans-serif;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    min-height: 40px;
    padding: 10px 16px;
}
QPushButton:hover {
    background: #e5e7eb;
}
QPushButton:pressed {
    background: #d1d5db;
}
QLabel#titleLabel {
    font-size: 22px;
    font-weight: 700;
}
QLineEdit, QDateEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 8px;
}
QTableView {
    background: #ffffff;
    border: 1px solid #d1d5db;
    gridline-color: #e5e7eb;
}
QHeaderView::section {
    background: #e5e7eb;
    padding: 8px;
    border: none;
}
QFrame#sidebar {
    background: #ffffff;
    border-right: 1px solid #d1d5db;
}
QPushButton#navButton {
    background: transparent;
    border: none;
    text-align: left;
    padding: 12px;
}
QPushButton#navButton:hover {
    background: #e5e7eb;
}
"""

dark_theme = """
QWidget {
    background: #111827;
    color: #e5e7eb;
    font-family: Segoe UI, Arial, sans-serif;
}
QPushButton {
    background: #1f2937;
    border: 1px solid #334155;
    border-radius: 12px;
    min-height: 40px;
    padding: 10px 16px;
}
QPushButton:hover {
    background: #374151;
}
QPushButton:pressed {
    background: #4b5563;
}
QLabel#titleLabel {
    font-size: 22px;
    font-weight: 700;
}
QLineEdit, QDateEdit, QComboBox {
    background: #1f2937;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px;
    color: #e5e7eb;
}
QTableView {
    background: #111827;
    border: 1px solid #334155;
    gridline-color: #374151;
}
QHeaderView::section {
    background: #1f2937;
    padding: 8px;
    border: none;
}
QFrame#sidebar {
    background: #111827;
    border-right: 1px solid #334155;
}
QPushButton#navButton {
    background: transparent;
    border: none;
    text-align: left;
    padding: 12px;
}
QPushButton#navButton:hover {
    background: #1f2937;
}
"""