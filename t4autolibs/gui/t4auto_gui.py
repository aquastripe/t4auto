import json
from pathlib import Path
from typing import NoReturn

from PySide6.QtWidgets import QWidget, QGridLayout, QMainWindow

from t4autolibs.cores import Agent
from t4autolibs.gui.item_table import ItemTable
from t4autolibs.gui.login import Login
from t4autolibs.gui.agent_status import AgentStatus
from t4autolibs.gui.window_size import WindowSize


class Composition(QWidget):

    def __init__(self, main_window: QMainWindow):
        super().__init__()

        self.main_window = main_window
        self.agent = Agent()
        self.window_size = WindowSize(self.main_window)
        self.item_table = ItemTable(self.agent)
        self.agent_status = AgentStatus()
        self.login = Login(self.agent, self.item_table, self.agent_status)

        # Compose all groups
        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.login.group, 0, 0)
        self.main_layout.addWidget(self.window_size.group, 0, 1)
        self.main_layout.addWidget(self.item_table.group, 1, 0, 1, 2)
        self.setLayout(self.main_layout)

    def load_config_from_file(self) -> NoReturn:
        config_file = Path('config.json')
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.window_size.load_config(config)
            self.item_table.load_config(config)
        else:
            self.item_table.add_empty_row()

    def dump_config_to_file(self) -> NoReturn:
        config = {}
        config |= self.window_size.dump_config()
        config |= self.item_table.dump_config()
        config_file = Path('config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
