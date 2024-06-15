from PySide6.QtWidgets import QWidget, QGridLayout

from t4autolibs.cores import Agent
from t4autolibs.gui.item_table import ItemTable
from t4autolibs.gui.login import Login
from t4autolibs.gui.window_size import WindowSize


class T4AutoGUI(QWidget):

    def __init__(self):
        super().__init__()

        self.agent = Agent()
        self.login = Login(self.agent)
        self.window_size = WindowSize(self)
        self.item_table = ItemTable(self.agent)

        # Compose all groups
        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.login.group, 0, 0)
        self.main_layout.addWidget(self.window_size.group, 0, 1)
        self.main_layout.addWidget(self.item_table.group, 1, 0, 1, 2)
        self.setLayout(self.main_layout)
