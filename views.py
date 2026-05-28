from datetime import date
import tempfile
import os
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QDate, QSize, QTimer, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpacerItem,
    QSpinBox,
    QStackedWidget,
    QTableView,
    QHeaderView,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)
from PySide6.QtGui import QStandardItem, QStandardItemModel, QIcon, QPixmap
from PySide6.QtWidgets import QSizePolicy

from controllers import AppController
from models import Clinic, Invoice, Payroll, Revenue
from style import dark_theme, light_theme


class SafeDateEdit(QDateEdit):
    """Custom QDateEdit that disables scroll wheel incrementing to prevent accidental date changes."""
    def wheelEvent(self, event):
        # Ignore wheel events - user must click calendar to change date
        event.ignore()


class MonthComboBox(QComboBox):
    """Custom QComboBox for selecting months in Polish."""
    MONTHS = [
        "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
        "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        for month in self.MONTHS:
            self.addItem(month)
    
    def set_month_text(self, text):
        """Set the selected month by text."""
        index = self.findText(text)
        if index >= 0:
            self.setCurrentIndex(index)
    
    def get_month_text(self):
        """Get the currently selected month."""
        return self.currentText()


class RecordDialog(QDialog):
    def __init__(self, title, fields, values=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.fields = fields
        self.values = values or {}
        self.inputs = {}
        self.setMinimumWidth(420)
        self.build_ui()

    def build_ui(self):
        layout = QFormLayout(self)
        for field in self.fields:
            name = field["name"]
            label = field["label"]
            field_type = field.get("type", "text")
            if field_type == "date":
                editor = SafeDateEdit()
                editor.setCalendarPopup(True)
                editor.setDisplayFormat("yyyy-MM-dd")
                editor.setDate(self.values.get(name, date.today()))
            elif field_type == "month":
                editor = MonthComboBox()
                month_value = self.values.get(name, "")
                if month_value:
                    editor.set_month_text(str(month_value))
            else:
                editor = QLineEdit()
                if field_type == "numeric":
                    editor.setPlaceholderText("0.00")
                editor.setText(str(self.values.get(name, "")))
            self.inputs[name] = editor
            layout.addRow(label, editor)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        result = {}
        for field in self.fields:
            name = field["name"]
            field_type = field.get("type", "text")
            widget = self.inputs[name]
            if field_type == "date":
                result[name] = widget.date().toPython()
            elif field_type == "month":
                result[name] = widget.get_month_text()
            elif field_type == "numeric":
                try:
                    result[name] = float(widget.text().replace(",", "."))
                except ValueError:
                    result[name] = None
            else:
                result[name] = widget.text().strip()
        return result

    def accept(self):
        data = self.get_data()
        for field in self.fields:
            value = data.get(field["name"])
            if field.get("type") == "numeric":
                if value is None:
                    QMessageBox.warning(self, "Walidacja", f"Pole {field['label']} musi być liczbą.")
                    return
            else:
                if not value:
                    QMessageBox.warning(self, "Walidacja", f"Pole {field['label']} jest wymagane.")
                    return
        super().accept()


class RecordPage(QWidget):
    data_changed = Signal()  # Emitted when data is added/edited
    
    def __init__(self, controller, clinic_id, config, location=None, clinic=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.clinic_id = clinic_id
        self.location = location
        self.clinic = clinic
        self.config = config
        self.items = []
        self.build_ui()
        self.refresh()
        
        # Auto-refresh timer for consistency
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(3000)  # Refresh every 3 seconds when widget is visible
    
    def showEvent(self, event):
        """Start auto-refresh when widget becomes visible."""
        super().showEvent(event)
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.start(3000)
    
    def hideEvent(self, event):
        """Stop auto-refresh when widget is hidden."""
        super().hideEvent(event)
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()

    def build_ui(self):
        layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        # title + breadcrumb stack
        title_box = QVBoxLayout()
        title = QLabel(self.config["title"])
        title.setObjectName("titleLabel")
        title_box.addWidget(title)
        # breadcrumb showing location and clinic if provided
        if hasattr(self, "location") and self.location and hasattr(self, "clinic") and self.clinic:
            breadcrumb = QLabel(f"{self.location.name} » {self.clinic.name}")
            breadcrumb.setObjectName("breadcrumbLabel")
            breadcrumb.setStyleSheet("color: #9ca3af; font-size: 12px;")
            title_box.addWidget(breadcrumb)
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        add_button = QPushButton(self.config["add_text"])
        add_button.clicked.connect(self.on_add)
        add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_layout.addWidget(add_button)
        export_button = QPushButton("Eksportuj do Excel")
        asset_dir = Path(__file__).parent / "assets"
        export_icon = asset_dir / "export.svg"
        if export_icon.exists():
            export_button.setIcon(QIcon(str(export_icon)))
            export_button.setIconSize(QSize(16, 16))
        export_button.clicked.connect(self.on_export)
        export_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_layout.addWidget(export_button)
        # add slight spacing below header
        layout.addLayout(header_layout)
        layout.addSpacing(8)

        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.config["search_placeholder"])
        self.search_input.textChanged.connect(self.refresh)
        filter_layout.addWidget(self.search_input)

        self.start_date = SafeDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        self.start_date.dateChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("Od"))
        filter_layout.addWidget(self.start_date)

        self.end_date = SafeDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        self.end_date.dateChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("Do"))
        filter_layout.addWidget(self.end_date)

        layout.addLayout(filter_layout)

        self.table = QTableView()
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.on_edit)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # allow multiple selection for batch operations
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # make table more spacious and responsive
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # style header and corner to match app colors
        try:
            self.table.setStyleSheet(
                "QHeaderView::section { background-color: #60a5fa; color: white; } QTableView::corner { background-color: #60a5fa; }")
        except Exception:
            pass
        layout.addWidget(self.table)

        actions_layout = QHBoxLayout()
        self.delete_button = QPushButton("Usuń zaznaczone")
        self.delete_button.clicked.connect(self.on_delete)
        actions_layout.addWidget(self.delete_button)
        actions_layout.addStretch()
        self.summary_label = QLabel()
        actions_layout.addWidget(self.summary_label)
        layout.addLayout(actions_layout)

    def refresh(self):
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        search_text = self.search_input.text().strip()
        self.items = self.config["fetch_fn"](self.clinic_id, start_date, end_date, search_text)
        self.update_table()
        self.update_summary()

    def update_table(self):
        model = QStandardItemModel(0, len(self.config["columns"]))
        model.setHorizontalHeaderLabels(self.config["columns"])
        for record in self.items:
            values = self.config["row_fn"](record)
            row = [QStandardItem(str(value)) for value in values]
            for item in row:
                item.setEditable(False)
            model.appendRow(row)
        self.table.setModel(model)
        # Force visual update
        self.table.viewport().update()
        
        # try to size columns to contents and then stretch to fill available space
        header = self.table.horizontalHeader()
        try:
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setStretchLastSection(True)
        except Exception:
            pass
        self.table.resizeColumnsToContents()
        # ensure reasonable minimum width
        try:
            winw = self.window().width()
            self.table.setMinimumWidth(max(800, int(winw * 0.6)))
        except Exception:
            self.table.setMinimumWidth(800)

    def update_summary(self):
        values = [self.config["summary_fn"](record) for record in self.items]
        total = sum(values)
        label = self.config.get("summary_label", "Suma")
        self.summary_label.setText(f"{label}: {total:,.2f} zł")

    def selected_records(self):
        sel = self.table.selectionModel().selectedRows()
        rows = [s.row() for s in sel]
        records = []
        for r in rows:
            if 0 <= r < len(self.items):
                records.append(self.items[r])
        return records

    def on_add(self):
        dialog = RecordDialog(self.config["dialog_title"], self.config["fields"], parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self.config["add_fn"](self.clinic_id, **data)
            self.refresh()

    def on_edit(self, index):
        # edit the double-clicked row
        row = index.row()
        if row < 0 or row >= len(self.items):
            return
        record = self.items[row]
        current_data = {field["name"]: getattr(record, field["name"]) for field in self.config["fields"]}
        dialog = RecordDialog(self.config["dialog_title"], self.config["fields"], values=current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self.config["update_fn"](record.id, data)
            self.refresh()

    def on_delete(self):
        records = self.selected_records()
        if not records:
            QMessageBox.information(self, "Usuń", "Wybierz rekordy do usunięcia.")
            return
        answer = QMessageBox.question(self, "Usuń rekordy", f"Czy na pewno usunąć {len(records)} zaznaczonych rekordów?")
        if answer == QMessageBox.StandardButton.Yes:
            for rec in records:
                self.config["delete_fn"](rec.id)
            self.refresh()

    def on_export(self):
        # include location, clinic and date range in filename
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        loc = (self.location.name if hasattr(self, 'location') and self.location else 'Location')
        clname = (self.clinic.name if hasattr(self, 'clinic') and self.clinic else f"Clinic_{self.clinic_id}")
        # Capitalize first letter of title
        title_text = self.config['title']
        title_text = title_text[0].upper() + title_text[1:].lower() if title_text else ""
        default_name = f"{loc}_{clname}_{start}_{end}_{title_text.replace(' ', '_')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Eksportuj do Excel", default_name, "Pliki Excel (*.xlsx)")
        if path:
            rows = [self.config["export_fn"](record) for record in self.items]
            self.config["export_to_excel"](rows, path)
            QMessageBox.information(self, "Eksport", "Dane zostały wyeksportowane do Excel.")


class AppMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = AppController()
        self.current_location = None
        self.current_clinic = None
        self.setWindowTitle("Menadżer Finansów Poradni")
        self.resize(1400, 900)
        self.theme = "dark"
        self.setStyleSheet(dark_theme)
        self.build_ui()
        self.show_home()

    def build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        # add some top margin so headers are not glued to window top
        main_layout.setContentsMargins(0, 16, 0, 0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        self.logo_label = QLabel("Poradnia Manager")
        self.logo_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        sidebar_layout.addWidget(self.logo_label)
        sidebar_layout.addSpacing(8)

        # Back button (disabled on home)
        self.back_button = QPushButton("Wstecz")
        self.back_button.setObjectName("navButton")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        # make back button more visible
        self.back_button.setStyleSheet("background-color: #2563eb; color: white; padding: 8px 12px; border-radius: 6px;")
        self.back_button.setMinimumHeight(48)
        self.back_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sidebar_layout.addWidget(self.back_button)

        self.home_button = QPushButton("Strona główna")
        self.home_button.setObjectName("navButton")
        self.home_button.clicked.connect(self.show_home)
        sidebar_layout.addWidget(self.home_button)

        self.analytics_button = QPushButton("Analiza finansowa")
        self.analytics_button.setObjectName("navButton")
        self.analytics_button.clicked.connect(self.show_analysis)
        sidebar_layout.addWidget(self.analytics_button)

        self.theme_button = QPushButton("Przełącz motyw")
        self.theme_button.setObjectName("navButton")
        self.theme_button.clicked.connect(self.toggle_theme)
        sidebar_layout.addWidget(self.theme_button)
        sidebar_layout.addStretch()

        main_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        # navigation history stack (stores previous widget refs)
        self.history = []
        main_layout.addWidget(self.stack, 1)

        self.home_page = self.build_home_page()
        self.stack.addWidget(self.home_page)

        self.clinic_page = QWidget()
        self.stack.addWidget(self.clinic_page)

        self.dashboard_page = QWidget()
        self.stack.addWidget(self.dashboard_page)

        self.analysis_page = self.build_analysis_page()
        self.stack.addWidget(self.analysis_page)

    def build_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Wybierz lokalizację")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        layout.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(20)
        locations = self.controller.get_locations()
        asset_dir = Path(__file__).parent / "assets"
        # mapping location names to specific icons
        loc_icons = {
            "Pruszków": asset_dir / "pruszkow.svg",
            "Żyrardów": asset_dir / "zyrardow.svg",
            "Zyrardow": asset_dir / "zyrardow.svg",
        }
        default_icon = asset_dir / "medical1.svg"
        for index, location in enumerate(locations):
            button = QPushButton(location.name)
            # larger, responsive tiles
            button.setMinimumHeight(200)
            button.setFont(QFont("Segoe UI", 16, QFont.Bold))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            icon_path = loc_icons.get(location.name, default_icon)
            if icon_path.exists():
                button.setIcon(QIcon(str(icon_path)))
                button.setIconSize(QSize(64, 64))
            button.clicked.connect(lambda checked, loc=location: self.show_clinic_list(loc))
            grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def build_clinic_list_page(self, location):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel(f"{location.name} — wybierz poradnię")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        layout.addSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QGridLayout(content)
        content_layout.setSpacing(16)
        clinics = self.controller.get_clinics(location.id)
        asset_dir = Path(__file__).parent / "assets"
        clinic_icon = asset_dir / "clinic.svg"
        for index, clinic in enumerate(clinics):
            button = QPushButton(clinic.name)
            # larger clinic tiles
            button.setMinimumHeight(180)
            button.setFont(QFont("Segoe UI", 14, QFont.Bold))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            if clinic_icon.exists():
                button.setIcon(QIcon(str(clinic_icon)))
                button.setIconSize(QSize(64, 64))
            button.clicked.connect(lambda checked, cl=clinic: self.show_dashboard(location, cl))
            content_layout.addWidget(button, index // 3, index % 3)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        layout.addStretch()
        return page

    def build_dashboard_page(self, location, clinic):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel(f"{location.name} / {clinic.name}")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        layout.addSpacing(12)

        button_layout = QHBoxLayout()
        asset_dir = Path(__file__).parent / "assets"
        icon_map = {
            "Faktury": asset_dir / "invoice.svg",
            "Wynagrodzenia": asset_dir / "payroll.svg",
            "Przychody": asset_dir / "revenue.svg",
            "Analiza finansowa": asset_dir / "analysis.svg",
        }
        for name, callback in [
            ("Faktury", self.show_invoices),
            ("Wynagrodzenia", self.show_payroll),
            ("Przychody", self.show_revenues),
            ("Analiza finansowa", self.show_analysis),
        ]:
            button = QPushButton(name)
            button.setMinimumHeight(220)
            button.setFont(QFont("Segoe UI", 14, QFont.Bold))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            icon_path = icon_map.get(name)
            if icon_path and icon_path.exists():
                button.setIcon(QIcon(str(icon_path)))
                button.setIconSize(QSize(64, 64))
            button.clicked.connect(callback)
            button_layout.addWidget(button)
        layout.addLayout(button_layout)

        # Export summary for the whole clinic
        export_layout = QHBoxLayout()
        export_summary_button = QPushButton("Eksport zestawienia poradni")
        export_summary_button.setMinimumHeight(48)
        export_summary_button.clicked.connect(lambda: self.export_clinic_summary(location, clinic))
        export_layout.addWidget(export_summary_button)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        # Improved summary section - professional dashboard style
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; padding: 16px;")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(12)
        
        summary_data = self.controller.get_financial_summary(clinic_id=clinic.id)
        
        # Title
        summary_title = QLabel("Podsumowanie finansowe")
        summary_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        summary_layout.addWidget(summary_title)
        
        # Grid with financial data
        data_layout = QGridLayout()
        data_layout.setSpacing(16)
        
        # Left column
        data_layout.addWidget(QLabel("Faktury netto:"), 0, 0)
        net_val = QLabel(f"{summary_data['invoice_net']:,.2f} zł")
        net_val.setFont(QFont("Segoe UI", 12, QFont.Bold))
        net_val.setStyleSheet("color: #3b82f6;")
        data_layout.addWidget(net_val, 0, 1)
        
        data_layout.addWidget(QLabel("Faktury brutto:"), 1, 0)
        gross_val = QLabel(f"{summary_data['invoice_gross']:,.2f} zł")
        gross_val.setFont(QFont("Segoe UI", 12, QFont.Bold))
        gross_val.setStyleSheet("color: #3b82f6;")
        data_layout.addWidget(gross_val, 1, 1)
        
        # Right column
        data_layout.addWidget(QLabel("Wynagrodzenia:"), 0, 2)
        payroll_val = QLabel(f"{summary_data['payroll']:,.2f} zł")
        payroll_val.setFont(QFont("Segoe UI", 12, QFont.Bold))
        payroll_val.setStyleSheet("color: #ef4444;")
        data_layout.addWidget(payroll_val, 0, 3)
        
        data_layout.addWidget(QLabel("Przychody:"), 1, 2)
        revenue_val = QLabel(f"{summary_data['revenue']:,.2f} zł")
        revenue_val.setFont(QFont("Segoe UI", 12, QFont.Bold))
        revenue_val.setStyleSheet("color: #10b981;")
        data_layout.addWidget(revenue_val, 1, 3)
        
        summary_layout.addLayout(data_layout)
        
        # Separator
        separator = QFrame()
        separator.setStyleSheet("background-color: #d1d5db; height: 2px;")
        separator.setFixedHeight(2)
        summary_layout.addWidget(separator)
        
        # Result - large and prominent
        result_layout = QHBoxLayout()
        result_label = QLabel("Wynik końcowy:")
        result_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        result_layout.addWidget(result_label)
        result_layout.addStretch()
        
        result_value = QLabel(f"{summary_data['profit']:,.2f} zł")
        result_value.setFont(QFont("Segoe UI", 18, QFont.Bold))
        
        # Color code result
        if summary_data['profit'] < 0:
            result_value.setStyleSheet("color: #dc2626; background-color: #fee2e2; padding: 12px 16px; border-radius: 6px;")
        else:
            result_value.setStyleSheet("color: #059669; background-color: #d1fae5; padding: 12px 16px; border-radius: 6px;")
        
        result_layout.addWidget(result_value)
        summary_layout.addLayout(result_layout)
        
        layout.addWidget(summary_frame)
        layout.addStretch()
        return page

    def build_analysis_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title section with padding
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #2563eb; padding: 16px;")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Analiza finansowa")
        title.setObjectName("titleLabel")
        title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        title_layout.addWidget(title)
        layout.addWidget(title_frame)
        
        # Controls section - compact
        controls_frame = QFrame()
        controls_frame.setStyleSheet("padding: 12px;")
        controls = QHBoxLayout(controls_frame)
        controls.setSpacing(12)
        controls.setContentsMargins(16, 12, 16, 12)
        
        self.location_select = QComboBox()
        self.location_select.addItem("Wszystkie lokalizacje", None)
        for location in self.controller.get_locations():
            self.location_select.addItem(location.name, location.id)
        self.location_select.currentIndexChanged.connect(self.update_analysis)
        lbl_loc = QLabel("Lokalizacja:")
        lbl_loc.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lbl_loc.setMaximumWidth(100)
        controls.addWidget(lbl_loc)
        controls.addWidget(self.location_select)

        self.clinic_select = QComboBox()
        self.clinic_select.addItem("Wszystkie poradnie", None)
        lbl_clinic = QLabel("Poradnia:")
        lbl_clinic.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lbl_clinic.setMaximumWidth(100)
        controls.addWidget(lbl_clinic)
        controls.addWidget(self.clinic_select)

        self.analysis_start = SafeDateEdit()
        self.analysis_start.setCalendarPopup(True)
        self.analysis_start.setDisplayFormat("yyyy-MM-dd")
        self.analysis_start.setDate(QDate.currentDate().addMonths(-3))
        self.analysis_start.dateChanged.connect(self.update_analysis)
        lbl_od = QLabel("Od: ")
        lbl_od.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lbl_od.setMaximumWidth(40)
        controls.addWidget(lbl_od)
        controls.addWidget(self.analysis_start)

        self.analysis_end = SafeDateEdit()
        self.analysis_end.setCalendarPopup(True)
        self.analysis_end.setDisplayFormat("yyyy-MM-dd")
        self.analysis_end.setDate(QDate.currentDate())
        self.analysis_end.dateChanged.connect(self.update_analysis)
        lbl_do = QLabel("Do: ")
        lbl_do.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lbl_do.setMaximumWidth(40)
        controls.addWidget(lbl_do)
        controls.addWidget(self.analysis_end)

        controls.addStretch()
        layout.addWidget(controls_frame)

        # Export analysis button - compact
        export_controls = QHBoxLayout()
        export_controls.setContentsMargins(16, 8, 16, 8)
        self.analysis_export_button = QPushButton("Eksport analizy")
        asset_dir = Path(__file__).parent / "assets"
        export_icon = asset_dir / "analysis.svg"
        if export_icon.exists():
            self.analysis_export_button.setIcon(QIcon(str(export_icon)))
            self.analysis_export_button.setIconSize(QSize(16, 16))
        self.analysis_export_button.setMaximumWidth(180)
        self.analysis_export_button.setMinimumHeight(36)
        self.analysis_export_button.clicked.connect(self.on_export_analysis)
        export_controls.addWidget(self.analysis_export_button)
        export_controls.addStretch()
        layout.addLayout(export_controls)

        # Summary section - larger fonts, better hierarchy
        summary_group = QGroupBox("Podsumowanie")
        summary_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 12px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setContentsMargins(16, 12, 16, 12)
        summary_layout.setSpacing(8)
        
        self.analysis_metrics = QLabel()
        self.analysis_metrics.setWordWrap(True)
        metrics_font = QFont("Segoe UI", 11)
        self.analysis_metrics.setFont(metrics_font)
        self.analysis_metrics.setStyleSheet("line-height: 1.6;")
        summary_layout.addWidget(self.analysis_metrics)
        layout.addWidget(summary_group)

        # Chart section - full width
        chart_group = QGroupBox("Wykresy")
        chart_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 12px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        chart_layout = QHBoxLayout(chart_group)
        chart_layout.setContentsMargins(16, 12, 16, 12)
        self.figure = Figure(figsize=(12, 5))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_group)

        layout.addStretch()

        self.location_select.currentIndexChanged.connect(self.populate_clinic_options)
        self.populate_clinic_options()
        self.update_analysis()
        return page

    def show_home(self):
        self.current_location = None
        self.current_clinic = None
        # clear navigation history when returning home
        self.history.clear()
        self.back_button.setEnabled(False)
        self.stack.setCurrentWidget(self.home_page)

    def show_clinic_list(self, location):
        self.current_location = location
        # push current view to history for back navigation
        cur = self.stack.currentWidget()
        if cur is not None:
            self.history.append(cur)
            self.back_button.setEnabled(True)
        clinic_list_page = self.build_clinic_list_page(location)
        self.stack.removeWidget(self.clinic_page)
        self.clinic_page = clinic_list_page
        self.stack.addWidget(self.clinic_page)
        self.stack.setCurrentWidget(self.clinic_page)

    def show_dashboard(self, location, clinic):
        self.current_location = location
        self.current_clinic = clinic
        # push current view to history
        cur = self.stack.currentWidget()
        if cur is not None:
            self.history.append(cur)
            self.back_button.setEnabled(True)
        dashboard_page = self.build_dashboard_page(location, clinic)
        self.stack.removeWidget(self.dashboard_page)
        self.dashboard_page = dashboard_page
        self.stack.addWidget(self.dashboard_page)
        self.stack.setCurrentWidget(self.dashboard_page)

    def show_invoices(self):
        if not self.current_clinic:
            QMessageBox.information(self, "Wybór poradni", "Najpierw wybierz poradnię.")
            return
        # push current view to history
        cur = self.stack.currentWidget()
        if cur is not None:
            self.history.append(cur)
            self.back_button.setEnabled(True)
        config = {
            "title": "Moduł faktur",
            "add_text": "Dodaj fakturę",
            "dialog_title": "Dodaj / Edytuj fakturę",
            "search_placeholder": "Szukaj numeru lub pozycji...",
            "columns": ["ID", "Numer faktury", "Pozycja", "Kategoria", "Firma", "Cena netto", "Cena brutto", "Data"],
            "fields": [
                {"name": "number", "label": "Numer faktury", "type": "text"},
                {"name": "item", "label": "Pozycja z faktury", "type": "text"},
                {"name": "category", "label": "Kategoria", "type": "text"},
                {"name": "company_name", "label": "Firma wystawiająca", "type": "text"},
                {"name": "net_amount", "label": "Cena netto", "type": "numeric"},
                {"name": "gross_amount", "label": "Cena brutto", "type": "numeric"},
                {"name": "date", "label": "Data", "type": "date"},
            ],
            "fetch_fn": self.controller.get_invoices,
            "add_fn": self.controller.add_invoice,
            "update_fn": lambda record_id, data: self.controller.update_record(Invoice, record_id, data),
            "delete_fn": lambda record_id: self.controller.delete_record(Invoice, record_id),
            "row_fn": lambda record: [record.id, record.number, record.item, getattr(record, 'category', ''), getattr(record, 'company_name', ''), f"{record.net_amount:.2f} zł", f"{record.gross_amount:.2f} zł", record.date],
            "summary_fn": lambda record: float(record.gross_amount),
            "summary_label": "Suma brutto",
            "export_fn": lambda record: {
                "ID": record.id,
                "Numer faktury": record.number,
                "Pozycja": record.item,
                "Kategoria": getattr(record, 'category', ''),
                "Firma": getattr(record, 'company_name', ''),
                "Cena netto": float(record.net_amount),
                "Cena brutto": float(record.gross_amount),
                "Data": record.date,
            },
            "export_to_excel": self.controller.export_to_excel,
        }
        page = RecordPage(self.controller, self.current_clinic.id, config, location=self.current_location, clinic=self.current_clinic)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def show_payroll(self):
        if not self.current_clinic:
            QMessageBox.information(self, "Wybór poradni", "Najpierw wybierz poradnię.")
            return
        # push current view to history
        cur = self.stack.currentWidget()
        if cur is not None:
            self.history.append(cur)
            self.back_button.setEnabled(True)
        config = {
            "title": "Moduł wynagrodzeń",
            "add_text": "Dodaj wynagrodzenie",
            "dialog_title": "Dodaj / Edytuj wynagrodzenie",
            "search_placeholder": "Szukaj pracownika...",
            "columns": ["ID", "Pracownik", "Miesiąc", "Kwota", "Data"],
            "fields": [
                {"name": "employee", "label": "Pracownik", "type": "text"},
                {"name": "period", "label": "Miesiąc", "type": "month"},
                {"name": "amount", "label": "Kwota", "type": "numeric"},
                {"name": "date", "label": "Data", "type": "date"},
            ],
            "fetch_fn": self.controller.get_payrolls,
            "add_fn": self.controller.add_payroll,
            "update_fn": lambda record_id, data: self.controller.update_record(Payroll, record_id, data),
            "delete_fn": lambda record_id: self.controller.delete_record(Payroll, record_id),
            "row_fn": lambda record: [record.id, record.employee, record.period, f"{record.amount:.2f} zł", record.date],
            "summary_fn": lambda record: float(record.amount),
            "summary_label": "Suma wynagrodzeń",
            "export_fn": lambda record: {
                "ID": record.id,
                "Pracownik": record.employee,
                "Miesiąc": record.period,
                "Kwota": float(record.amount),
                "Data": record.date,
            },
            "export_to_excel": self.controller.export_to_excel,
        }
        page = RecordPage(self.controller, self.current_clinic.id, config, location=self.current_location, clinic=self.current_clinic)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def show_revenues(self):
        if not self.current_clinic:
            QMessageBox.information(self, "Wybór poradni", "Najpierw wybierz poradnię.")
            return
        # push current view to history
        cur = self.stack.currentWidget()
        if cur is not None:
            self.history.append(cur)
            self.back_button.setEnabled(True)
        config = {
            "title": "Moduł przychodów",
            "add_text": "Dodaj przychód",
            "dialog_title": "Dodaj / Edytuj przychód",
            "search_placeholder": "Szukaj firmy...",
            "columns": ["ID", "Firma", "Miesiąc", "Kwota", "Data"],
            "fields": [
                {"name": "company", "label": "Firma", "type": "text"},
                {"name": "period", "label": "Miesiąc", "type": "month"},
                {"name": "amount", "label": "Kwota", "type": "numeric"},
                {"name": "date", "label": "Data", "type": "date"},
            ],
            "fetch_fn": self.controller.get_revenues,
            "add_fn": self.controller.add_revenue,
            "update_fn": lambda record_id, data: self.controller.update_record(Revenue, record_id, data),
            "delete_fn": lambda record_id: self.controller.delete_record(Revenue, record_id),
            "row_fn": lambda record: [record.id, record.company, record.period, f"{record.amount:.2f} zł", record.date],
            "summary_fn": lambda record: float(record.amount),
            "summary_label": "Suma przychodów",
            "export_fn": lambda record: {
                "ID": record.id,
                "Firma": record.company,
                "Miesiąc": record.period,
                "Kwota": float(record.amount),
                "Data": record.date,
            },
            "export_to_excel": self.controller.export_to_excel,
        }
        page = RecordPage(self.controller, self.current_clinic.id, config, location=self.current_location, clinic=self.current_clinic)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def show_analysis(self):
        self.stack.setCurrentWidget(self.analysis_page)

    def toggle_theme(self):
        if self.theme == "dark":
            self.theme = "light"
            self.setStyleSheet(light_theme)
        else:
            self.theme = "dark"
            self.setStyleSheet(dark_theme)

    def go_back(self):
        if not hasattr(self, "history") or not self.history:
            return
        prev = self.history.pop()
        # If the previous widget was the home page, clear navigation state
        if prev == getattr(self, "home_page", None):
            self.current_location = None
            self.current_clinic = None
            self.history.clear()
            self.back_button.setEnabled(False)
        elif not self.history:
            # disable back button when no more history
            self.back_button.setEnabled(False)
        self.stack.setCurrentWidget(prev)

    def populate_clinic_options(self):
        location_id = self.location_select.currentData()
        self.clinic_select.blockSignals(True)
        self.clinic_select.clear()
        self.clinic_select.addItem("Wszystkie poradnie", None)
        if location_id:
            clinics = self.controller.get_clinics(location_id)
            for clinic in clinics:
                self.clinic_select.addItem(clinic.name, clinic.id)
        self.clinic_select.blockSignals(False)
        self.clinic_select.currentIndexChanged.connect(self.update_analysis)
        self.update_analysis()

    def update_analysis(self):
        location_id = self.location_select.currentData()
        clinic_id = self.clinic_select.currentData()
        start_date = self.analysis_start.date().toPython()
        end_date = self.analysis_end.date().toPython()
        stats = self.controller.get_financial_summary(location_id=location_id, clinic_id=clinic_id, start_date=start_date, end_date=end_date)
        
        # Better formatted text with HTML for hierarchy
        metrics_text = f"""<b>Okres:</b> {start_date} — {end_date}<br><br>
<b>Faktury:</b><br>
  Netto: <b>{stats['invoice_net']:,.2f} zł</b><br>
  Brutto: <b>{stats['invoice_gross']:,.2f} zł</b><br><br>
<b>Wynagrodzenia:</b> <b>{stats['payroll']:,.2f} zł</b><br><br>
<b>Przychody:</b> <b>{stats['revenue']:,.2f} zł</b><br><br>
<b>Wynik końcowy:</b> <span style="font-size: 14pt; font-weight: bold;">{stats['profit']:,.2f} zł</span>"""
        
        self.analysis_metrics.setText(metrics_text)
        self.plot_analysis(stats)

    def plot_analysis(self, stats):
        # Modern chart appearance with better hierarchy
        self.figure.clear()
        self.figure.patch.set_facecolor("white")
        
        # Create subplots with better spacing
        axes = self.figure.subplots(1, 2, gridspec_kw={'width_ratios': [1, 1]})
        self.figure.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.12)
        
        # Bar chart - categories
        cats = ["Faktury netto", "Wynagrodzenia", "Przychody"]
        values = [stats["invoice_net"], stats["payroll"], stats["revenue"]]
        colors = ["#3b82f6", "#ef4444", "#10b981"]
        bars = axes[0].bar(cats, values, color=colors, edgecolor="none", alpha=0.85)
        axes[0].set_title("Rozkład wydatków i przychodów", fontsize=13, fontweight='bold', pad=12)
        axes[0].grid(axis="y", alpha=0.2, linestyle="--")
        axes[0].set_ylabel("Kwota (zł)", fontsize=10, fontweight='bold')
        axes[0].set_facecolor("#f8f9fa")
        
        # Annotate bars with values
        for bar, value in zip(bars, values):
            height = bar.get_height()
            if height != 0:  # Only annotate non-zero values
                axes[0].text(bar.get_x() + bar.get_width()/2., height,
                            f'{value:,.0f} zł',
                            ha='center', va='bottom', fontsize=9, fontweight='bold')
        axes[0].tick_params(axis='x', labelsize=9)
        axes[0].tick_params(axis='y', labelsize=9)
        
        # Pie chart - result breakdown
        if stats['revenue'] > 0:
            pie_labels = ['Przychody', 'Koszty']
            pie_values = [stats['revenue'], stats['payroll'] + stats['invoice_net']]
            pie_colors = ['#10b981', '#f87171']
            wedges, texts, autotexts = axes[1].pie(pie_values, labels=pie_labels, autopct='%1.1f%%',
                                                    colors=pie_colors, startangle=90, textprops={'fontsize': 10})
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            axes[1].set_title("Proporcja przychodów vs kosztów", fontsize=13, fontweight='bold', pad=12)
        
        self.figure.tight_layout()
        self.canvas.draw()

    def export_clinic_summary(self, location, clinic):
        default_name = f"{clinic.name.replace(' ', '_')}_Zestawienie.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Eksport zestawienia poradni", default_name, "Excel Files (*.xlsx)")
        if path:
            self.controller.export_clinic_summary(clinic.id, path)
            QMessageBox.information(self, "Eksport", "Zestawienie poradni zostało wyeksportowane.")

    def on_export_analysis(self):
        # gather current filters and data then export
        location_id = self.location_select.currentData()
        clinic_id = self.clinic_select.currentData()
        start_date = self.analysis_start.date().toPython()
        end_date = self.analysis_end.date().toPython()
        
        # Capitalize location and clinic names in filename
        loc_text = self.location_select.currentText()
        clinic_text = self.clinic_select.currentText()
        default_name = f"Analiza_{loc_text.replace(' ', '_')}_{clinic_text.replace(' ', '_')}_{start_date}_{end_date}.xlsx"
        
        path, _ = QFileDialog.getSaveFileName(self, "Eksport analizy", default_name, "Pliki Excel (*.xlsx)")
        if not path:
            return
        # save current figure to temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()
        self.figure.savefig(tmp.name, dpi=150)

        # fetch records for sheets
        invs = []
        pays = []
        revs = []
        # if clinic selected, fetch from that clinic; if only location selected, fetch for all clinics in location
        if clinic_id:
            invs = self.controller.get_invoices(clinic_id, start_date, end_date)
            pays = self.controller.get_payrolls(clinic_id, start_date, end_date)
            revs = self.controller.get_revenues(clinic_id, start_date, end_date)
        else:
            # aggregate from all clinics under location or all
            loc_id = location_id
            clinics = []
            if loc_id:
                clinics = self.controller.get_clinics(loc_id)
            else:
                clinics = self.controller.get_clinics()
            for c in clinics:
                invs.extend(self.controller.get_invoices(c.id, start_date, end_date))
                pays.extend(self.controller.get_payrolls(c.id, start_date, end_date))
                revs.extend(self.controller.get_revenues(c.id, start_date, end_date))

        # build clinic id->name map to avoid lazy-loading detached relationships
        clinics_map = {c.id: c.name for c in self.controller.get_clinics()}
        # build dataframes
        import pandas as pd

        df_inv = pd.DataFrame([{
            "ID": r.id,
            "Numer": r.number,
            "Pozycja": r.item,
            "Cena netto": float(r.net_amount),
            "Cena brutto": float(r.gross_amount),
            "Data": r.date,
            "Poradnia": clinics_map.get(getattr(r, 'clinic_id', None), '')
        } for r in invs])

        df_pay = pd.DataFrame([{
            "ID": r.id,
            "Pracownik": r.employee,
            "Miesiąc": r.period,
            "Kwota": float(r.amount),
            "Data": r.date,
            "Poradnia": clinics_map.get(getattr(r, 'clinic_id', None), '')
        } for r in pays])

        df_rev = pd.DataFrame([{
            "ID": r.id,
            "Firma": r.company,
            "Miesiąc": r.period,
            "Kwota": float(r.amount),
            "Data": r.date,
            "Poradnia": clinics_map.get(getattr(r, 'clinic_id', None), '')
        } for r in revs])

        metadata = {
            "Lokalizacja": self.location_select.currentText(),
            "Poradnia": self.clinic_select.currentText(),
            "Start": str(start_date),
            "Koniec": str(end_date),
        }

        # use controller export helper
        self.controller.export_report(path, {"Podsumowanie": pd.DataFrame([self.controller.get_financial_summary(location_id=location_id, clinic_id=clinic_id, start_date=start_date, end_date=end_date)]), "Faktury": df_inv, "Wynagrodzenia": df_pay, "Przychody": df_rev}, tmp.name, metadata)
        QMessageBox.information(self, "Eksport", "Analiza została wyeksportowana do Excel.")
        try:
            os.remove(tmp.name)
        except Exception:
            pass

