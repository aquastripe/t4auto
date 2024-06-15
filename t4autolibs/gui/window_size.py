from dataclasses import dataclass
from functools import partial
from typing import NoReturn

from PySide6.QtWidgets import QWidget, QVBoxLayout, QRadioButton, QGroupBox

from t4autolibs.gui.config import Configurable


@dataclass
class SizeInfo:
    idx: int
    display_name: str
    size: tuple[int, int]


IDX_MAXIMIZE_WINDOW = 3


class WindowSize(Configurable):
    _SIZE_INFO_LIST = [
        SizeInfo(0, '800 × 600', (800, 600)),
        SizeInfo(1, '1024 × 768', (1024, 768)),
        SizeInfo(2, '1920 × 1080', (1920, 1080)),
        SizeInfo(IDX_MAXIMIZE_WINDOW, 'Maximize', (0, 0)),
    ]

    def __init__(self, parent_window: QWidget):
        self.size_info = self._SIZE_INFO_LIST[0]
        self.parent_window = parent_window
        self.resize_main_window(self._SIZE_INFO_LIST[0])
        self.window_size_layout = QVBoxLayout()

        first_button_is_checked = False
        self.buttons = []
        for size_info in self._SIZE_INFO_LIST:
            button = QRadioButton(size_info.display_name)
            if not first_button_is_checked:
                button.setChecked(True)
                first_button_is_checked = True

            specified_resize_main_window = partial(self.resize_main_window, size_info=size_info)
            button.clicked.connect(specified_resize_main_window)
            self.window_size_layout.addWidget(button)
            self.buttons.append(button)

        self.group = QGroupBox('Window Size')
        self.group.setLayout(self.window_size_layout)

    def resize_main_window(self, size_info: SizeInfo):
        self.size_info = size_info
        if self.size_info.idx == IDX_MAXIMIZE_WINDOW:
            self.parent_window.showMaximized()
        else:
            self.parent_window.resize(*self.size_info.size)

    def load_config(self, config: dict) -> NoReturn:
        if config['WindowSize'] is None:
            return

        if config['WindowSize'] >= len(self._SIZE_INFO_LIST):
            print(f'config.json Warning: The WindowSize is too large. It should be < {len(self._SIZE_INFO_LIST)}.')
            return

        size_info = self._SIZE_INFO_LIST[config['WindowSize']]
        self.buttons[size_info.idx].click()

    def dump_config(self) -> dict:
        config = {
            'WindowSize': self.size_info.idx,
        }
        return config
