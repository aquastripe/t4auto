from dataclasses import dataclass
from functools import partial
from typing import NoReturn

from PySide6.QtWidgets import QWidget, QVBoxLayout, QRadioButton, QGroupBox

from t4autolibs.gui.config import Configurable

FLAG_MAXIMIZE = 0


@dataclass
class SizeInfo:
    display_name: str
    size: [tuple[int, int], int]


class WindowSize(Configurable):
    _SIZE_INFO_LIST = [
        SizeInfo('800 × 600', (800, 600)),
        SizeInfo('1024 × 768', (1024, 768)),
        SizeInfo('1920 × 1080', (1920, 1080)),
        SizeInfo('Maximize', FLAG_MAXIMIZE),
    ]

    def __init__(self, parent_window: QWidget):
        self.size = self._SIZE_INFO_LIST[0].size
        self.parent_window = parent_window
        self.resize_main_window(self.size)
        self.window_size_layout = QVBoxLayout()

        first_button_is_checked = False
        for size_info in self._SIZE_INFO_LIST:
            button = QRadioButton(size_info.display_name)
            if not first_button_is_checked:
                button.setChecked(True)
                first_button_is_checked = True

            specified_resize_main_window = partial(self.resize_main_window, size=size_info.size)
            button.clicked.connect(specified_resize_main_window)
            self.window_size_layout.addWidget(button)

        self.group = QGroupBox('Window Size')
        self.group.setLayout(self.window_size_layout)

    def resize_main_window(self, size):
        self.size = size
        if self.size == FLAG_MAXIMIZE:
            self.parent_window.showMaximized()
        else:
            self.parent_window.resize(*self.size)

    def load_config(self, config: dict) -> NoReturn:
        if config['WindowSize'] is None:
            return

        self.resize_main_window(config['WindowSize'])

    def dump_config(self) -> dict:
        config = {
            'WindowSize': self.size,
        }
        return config
