import sys

from PySide6.QtWidgets import QApplication

from t4autolibs.gui.t4auto_gui import T4AutoGUI


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('T4 Auto')
    t4auto_gui = T4AutoGUI()
    t4auto_gui.resize(800, 600)
    t4auto_gui.show()
    app.exec()


if __name__ == '__main__':
    main()
