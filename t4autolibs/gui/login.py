from dataclasses import dataclass
from typing import NoReturn

from PySide6 import QtGui
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QHBoxLayout, QCheckBox, QPushButton, QVBoxLayout, \
    QRadioButton, QWidget

from t4autolibs.cores import UserInfo, LoginStatus
from t4autolibs.gui.config import Configurable
from functools import partial


class Login:

    def __init__(self, agent):
        self.agent = agent

        self.layout = QFormLayout()
        self.group = QGroupBox('Login info')
        self.group.setLayout(self.layout)

        # Login group / username, password
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addRow('Username', self.username_edit)
        self.layout.addRow('Password', self.password_edit)

        # Login group / save username, show password
        self.checkbox_layout = QHBoxLayout()
        self.save_username = QCheckBox('Save username')
        self.save_username.setEnabled(False)  # TODO: future feature
        self.checkbox_layout.addWidget(self.save_username)

        self.display_password = QCheckBox('Show password')
        self.display_password.stateChanged.connect(self.show_password)
        self.checkbox_layout.addWidget(self.display_password)

        self._is_logged_in = False
        self.login_button = QPushButton('Login')
        self.login_button.setIcon(QtGui.QIcon('_internal/icons/login.svg'))
        self.login_button.clicked.connect(self.login)
        self.checkbox_layout.addWidget(self.login_button)

        self.logout_button = QPushButton('Logout')
        self.logout_button.setIcon(QtGui.QIcon('_internal/icons/logout.svg'))
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setEnabled(False)
        self.checkbox_layout.addWidget(self.logout_button)

        self.layout.addRow(self.checkbox_layout)

    @Slot(int)
    def show_password(self, state):
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        elif Qt.CheckState(state) == Qt.CheckState.Unchecked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    @Slot()
    def login(self):
        self._unset_login_button()
        if not self._is_logged_in:
            self._is_logged_in = True
            user_info = UserInfo(self.username_edit.text(), self.password_edit.text())
            login_status = self.agent.login(user_info)  # type: LoginStatus

            # TODO: show message
            if login_status.success:
                ...
            else:
                self._set_login_button()

    @Slot()
    def logout(self):
        self._set_login_button()
        if self._is_logged_in:
            self._is_logged_in = False
            self.agent.logout()

    def _set_login_button(self):
        self.login_button.setEnabled(True)
        self.logout_button.setEnabled(False)

    def _unset_login_button(self):
        self.login_button.setEnabled(False)
        self.logout_button.setEnabled(True)


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

        self.resize_main_window(tuple(config['WindowSize']))

    def dump_config(self) -> dict:
        config = {
            'WindowSize': self.size,
        }
        return config
