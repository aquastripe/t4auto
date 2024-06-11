import sys

from PySide6.QtWidgets import QApplication, QWidget, QGridLayout

from t4autolibs.gui.item_table import ItemTable
from t4autolibs.gui.login import Login, Browser
from t4autolibs.cores import Agent


class T4AutoGUI(QWidget):

    def __init__(self):
        super().__init__()

        self.agent = Agent()
        self.login = Login(self.agent)
        self.browser = Browser()
        self.item_table = ItemTable(self.agent)

        # Compose all groups
        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.login.group, 0, 0)
        self.main_layout.addWidget(self.browser.group, 0, 1)
        self.main_layout.addWidget(self.item_table.group, 1, 0, 1, 2)
        self.setLayout(self.main_layout)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('T4 Auto')
    t4auto_gui = T4AutoGUI()
    t4auto_gui.resize(800, 600)
    t4auto_gui.show()
    app.exec()


if __name__ == '__main__':
    main()
