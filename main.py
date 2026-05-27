import sys

from PySide6.QtWidgets import QApplication

from views import AppMainWindow


def main():
    app = QApplication(sys.argv)
    window = AppMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
