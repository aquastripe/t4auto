import sys

from PySide6.QtWidgets import QApplication

from t4autolibs.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('T4 Auto')
    main_window = MainWindow()
    main_window.load_config_from_file()
    main_window.show()
    app.exec()
    main_window.dump_config_to_file()


if __name__ == '__main__':
    main()
