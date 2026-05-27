from datetime import date
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QDate
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
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QStandardItem, QStandardItemModel

from controllers import AppController
from models import Clinic, Invoice, Payroll, Revenue
from style import dark_theme, light_theme


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
                editor = QDateEdit()
                editor.setCalendarPopup(True)
                editor.setDisplayFormat("yyyy-MM-dd")
                editor.setDate(self.values.get(name, date.today()))
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
    def __init__(self, controller, clinic_id, config, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.clinic_id = clinic_id
        self.config = config
        self.items = []
        self.build_ui()
        self.refresh()

    def build_ui(self):
        layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        title = QLabel(self.config["title"])
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        header_layout.addStretch()
        add_button = QPushButton(self.config["add_text"])
        add_button.clicked.connect(self.on_add)
        header_layout.addWidget(add_button)
        export_button = QPushButton("Eksportuj do Excel")
        export_button.clicked.connect(self.on_export)
        header_layout.addWidget(export_button)
        layout.addLayout(header_layout)

        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.config["search_placeholder"])
        self.search_input.textChanged.connect(self.refresh)
        filter_layout.addWidget(self.search_input)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        self.start_date.dateChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("Od"))
        filter_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
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
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
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
        self.table.resizeColumnsToContents()

    def update_summary(self):
        values = [self.config["summary_fn"](record) for record in self.items]
        total = sum(values)
        label = self.config.get("summary_label", "Suma")
        self.summary_label.setText(f"{label}: {total:,.2f}")

    def selected_record(self):
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self.items):
            return None
        return self.items[row]

    def on_add(self):
        dialog = RecordDialog(self.config["dialog_title"], self.config["fields"], parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self.config["add_fn"](self.clinic_id, **data)
            self.refresh()

    def on_edit(self, index):
        record = self.selected_record()
        if record is None:
            return
        current_data = {field["name"]: getattr(record, field["name"]) for field in self.config["fields"]}
        dialog = RecordDialog(self.config["dialog_title"], self.config["fields"], values=current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self.config["update_fn"](record.id, data)
            self.refresh()

    def on_delete(self):
        record = self.selected_record()
        if not record:
            QMessageBox.information(self, "Usuń", "Wybierz rekord do usunięcia.")
            return
        answer = QMessageBox.question(self, "Usuń rekord", "Czy na pewno usunąć zaznaczony rekord?")
        if answer == QMessageBox.StandardButton.Yes:
            self.config["delete_fn"](record.id)
            self.refresh()

    def on_export(self):
        default_name = f"{self.config['title'].lower().replace(' ', '_')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Eksportuj do Excel", default_name, "Excel Files (*.xlsx)")
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
        self.setWindowTitle("Poradnia Finance Manager")
        self.resize(1400, 900)
        self.theme = "dark"
        self.setStyleSheet(dark_theme)
        self.build_ui()
        self.show_home()

    def build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

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
        for index, location in enumerate(locations):
            button = QPushButton(location.name)
            button.setMinimumHeight(140)
            button.setFont(QFont("Segoe UI", 14, QFont.Bold))
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
        for index, clinic in enumerate(clinics):
            button = QPushButton(clinic.name)
            button.setMinimumHeight(100)
            button.setFont(QFont("Segoe UI", 12, QFont.Bold))
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
        for name, callback in [
            ("Faktury", self.show_invoices),
            ("Wynagrodzenia", self.show_payroll),
            ("Przychody", self.show_revenues),
            ("Analiza finansowa", self.show_analysis),
        ]:
            button = QPushButton(name)
            button.setMinimumHeight(100)
            button.clicked.connect(callback)
            button_layout.addWidget(button)
        layout.addLayout(button_layout)

        summary = QLabel()
        summary.setWordWrap(True)
        layout.addWidget(summary)
        summary_data = self.controller.get_financial_summary(clinic_id=clinic.id)
        summary.setText(
            f"Suma faktur netto: {summary_data['invoice_net']:,.2f}  |  "
            f"Suma faktur brutto: {summary_data['invoice_gross']:,.2f}\n"
            f"Suma wynagrodzeń: {summary_data['payroll']:,.2f}  |  "
            f"Suma przychodów: {summary_data['revenue']:,.2f}  |  "
            f"Wynik: {summary_data['profit']:,.2f}"
        )
        layout.addStretch()
        return page

    def build_analysis_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Analiza finansowa")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        layout.addSpacing(12)

        controls = QHBoxLayout()
        self.location_select = QComboBox()
        self.location_select.addItem("Wszystkie lokalizacje", None)
        for location in self.controller.get_locations():
            self.location_select.addItem(location.name, location.id)
        self.location_select.currentIndexChanged.connect(self.update_analysis)
        controls.addWidget(QLabel("Lokalizacja"))
        controls.addWidget(self.location_select)

        self.clinic_select = QComboBox()
        self.clinic_select.addItem("Wszystkie poradnie", None)
        controls.addWidget(QLabel("Poradnia"))
        controls.addWidget(self.clinic_select)

        self.analysis_start = QDateEdit()
        self.analysis_start.setCalendarPopup(True)
        self.analysis_start.setDisplayFormat("yyyy-MM-dd")
        self.analysis_start.setDate(QDate.currentDate().addMonths(-3))
        self.analysis_start.dateChanged.connect(self.update_analysis)
        controls.addWidget(QLabel("Od"))
        controls.addWidget(self.analysis_start)

        self.analysis_end = QDateEdit()
        self.analysis_end.setCalendarPopup(True)
        self.analysis_end.setDisplayFormat("yyyy-MM-dd")
        self.analysis_end.setDate(QDate.currentDate())
        self.analysis_end.dateChanged.connect(self.update_analysis)
        controls.addWidget(QLabel("Do"))
        controls.addWidget(self.analysis_end)

        layout.addLayout(controls)

        summary_group = QGroupBox("Podsumowanie")
        summary_layout = QVBoxLayout(summary_group)
        self.analysis_metrics = QLabel()
        self.analysis_metrics.setWordWrap(True)
        summary_layout.addWidget(self.analysis_metrics)
        layout.addWidget(summary_group)

        chart_group = QGroupBox("Wykresy")
        chart_layout = QHBoxLayout(chart_group)
        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_group)

        self.location_select.currentIndexChanged.connect(self.populate_clinic_options)
        self.populate_clinic_options()
        self.update_analysis()
        return page

    def show_home(self):
        self.current_location = None
        self.current_clinic = None
        self.stack.setCurrentWidget(self.home_page)

    def show_clinic_list(self, location):
        self.current_location = location
        clinic_list_page = self.build_clinic_list_page(location)
        self.stack.removeWidget(self.clinic_page)
        self.clinic_page = clinic_list_page
        self.stack.addWidget(self.clinic_page)
        self.stack.setCurrentWidget(self.clinic_page)

    def show_dashboard(self, location, clinic):
        self.current_location = location
        self.current_clinic = clinic
        dashboard_page = self.build_dashboard_page(location, clinic)
        self.stack.removeWidget(self.dashboard_page)
        self.dashboard_page = dashboard_page
        self.stack.addWidget(self.dashboard_page)
        self.stack.setCurrentWidget(self.dashboard_page)

    def show_invoices(self):
        if not self.current_clinic:
            QMessageBox.information(self, "Wybór poradni", "Najpierw wybierz poradnię.")
            return
        config = {
            "title": "Moduł faktur",
            "add_text": "Dodaj fakturę",
            "dialog_title": "Dodaj / Edytuj fakturę",
            "search_placeholder": "Szukaj numeru lub pozycji...",
            "columns": ["ID", "Numer faktury", "Pozycja", "Cena netto", "Cena brutto", "Data"],
            "fields": [
                {"name": "number", "label": "Numer faktury", "type": "text"},
                {"name": "item", "label": "Pozycja z faktury", "type": "text"},
                {"name": "net_amount", "label": "Cena netto", "type": "numeric"},
                {"name": "gross_amount", "label": "Cena brutto", "type": "numeric"},
                {"name": "date", "label": "Data", "type": "date"},
            ],
            "fetch_fn": self.controller.get_invoices,
            "add_fn": self.controller.add_invoice,
            "update_fn": lambda record_id, data: self.controller.update_record(Invoice, record_id, data),
            "delete_fn": lambda record_id: self.controller.delete_record(Invoice, record_id),
            "row_fn": lambda record: [record.id, record.number, record.item, f"{record.net_amount:.2f}", f"{record.gross_amount:.2f}", record.date],
            "summary_fn": lambda record: float(record.net_amount),
            "summary_label": "Suma netto",
            "export_fn": lambda record: {
                "ID": record.id,
                "Numer faktury": record.number,
                "Pozycja": record.item,
                "Cena netto": float(record.net_amount),
                "Cena brutto": float(record.gross_amount),
                "Data": record.date,
            },
            "export_to_excel": self.controller.export_to_excel,
        }
        page = RecordPage(self.controller, self.current_clinic.id, config)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def show_payroll(self):
        if not self.current_clinic:
            QMessageBox.information(self, "Wybór poradni", "Najpierw wybierz poradnię.")
            return
        config = {
            "title": "Moduł wynagrodzeń",
            "add_text": "Dodaj wynagrodzenie",
            "dialog_title": "Dodaj / Edytuj wynagrodzenie",
            "search_placeholder": "Szukaj pracownika...",
            "columns": ["ID", "Pracownik", "Miesiąc", "Kwota", "Data"],
            "fields": [
                {"name": "employee", "label": "Pracownik", "type": "text"},
                {"name": "period", "label": "Miesiąc", "type": "text"},
                {"name": "amount", "label": "Kwota", "type": "numeric"},
                {"name": "date", "label": "Data", "type": "date"},
            ],
            "fetch_fn": self.controller.get_payrolls,
            "add_fn": self.controller.add_payroll,
            "update_fn": lambda record_id, data: self.controller.update_record(Payroll, record_id, data),
            "delete_fn": lambda record_id: self.controller.delete_record(Payroll, record_id),
            "row_fn": lambda record: [record.id, record.employee, record.period, f"{record.amount:.2f}", record.date],
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
        page = RecordPage(self.controller, self.current_clinic.id, config)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def show_revenues(self):
        if not self.current_clinic:
            QMessageBox.information(self, "Wybór poradni", "Najpierw wybierz poradnię.")
            return
        config = {
            "title": "Moduł przychodów",
            "add_text": "Dodaj przychód",
            "dialog_title": "Dodaj / Edytuj przychód",
            "search_placeholder": "Szukaj firmy...",
            "columns": ["ID", "Firma", "Miesiąc", "Kwota", "Data"],
            "fields": [
                {"name": "company", "label": "Firma", "type": "text"},
                {"name": "period", "label": "Miesiąc", "type": "text"},
                {"name": "amount", "label": "Kwota", "type": "numeric"},
                {"name": "date", "label": "Data", "type": "date"},
            ],
            "fetch_fn": self.controller.get_revenues,
            "add_fn": self.controller.add_revenue,
            "update_fn": lambda record_id, data: self.controller.update_record(Revenue, record_id, data),
            "delete_fn": lambda record_id: self.controller.delete_record(Revenue, record_id),
            "row_fn": lambda record: [record.id, record.company, record.period, f"{record.amount:.2f}", record.date],
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
        page = RecordPage(self.controller, self.current_clinic.id, config)
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
        try:
            self.clinic_select.currentIndexChanged.disconnect(self.update_analysis)
        except Exception:
            pass
        self.clinic_select.currentIndexChanged.connect(self.update_analysis)
        self.update_analysis()

    def update_analysis(self):
        location_id = self.location_select.currentData()
        clinic_id = self.clinic_select.currentData()
        start_date = self.analysis_start.date().toPython()
        end_date = self.analysis_end.date().toPython()
        stats = self.controller.get_financial_summary(location_id=location_id, clinic_id=clinic_id, start_date=start_date, end_date=end_date)
        self.analysis_metrics.setText(
            f"Okres: {start_date} — {end_date}\n"
            f"Suma faktur netto: {stats['invoice_net']:,.2f}\n"
            f"Suma faktur brutto: {stats['invoice_gross']:,.2f}\n"
            f"Suma wynagrodzeń: {stats['payroll']:,.2f}\n"
            f"Suma przychodów: {stats['revenue']:,.2f}\n"
            f"Wynik końcowy: {stats['profit']:,.2f}"
        )
        self.plot_analysis(stats)

    def plot_analysis(self, stats):
        self.figure.clear()
        axes = self.figure.subplots(1, 2)
        axes[0].bar(["Faktury netto", "Wynagrodzenia", "Przychody"], [stats["invoice_net"], stats["payroll"], stats["revenue"]], color=["#3b82f6", "#ef4444", "#10b981"])
        axes[0].set_title("Suma kategorii")
        axes[0].grid(axis="y", alpha=0.3)
        axes[1].plot(["Start", "Koniec"], [stats["invoice_gross"], stats["profit"]], marker="o", color="#f59e0b")
        axes[1].set_title("Trend wyników")
        axes[1].grid(alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()
