from PySide6 import QtGui
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QHBoxLayout, QCheckBox, QPushButton, QVBoxLayout, \
    QRadioButton

from t4autolibs.cores import UserInfo, LoginStatus


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


class WindowSize:
    _SIZES = [
        ('800 × 600', (800, 600)),
        ('1024 × 768', (1024, 768)),
        ('1920 × 1080', (1920, 1080)),
    ]

    def __init__(self):
        self.window_size_layout = QVBoxLayout()

        first_button_is_checked = False
        for size in self._SIZES:
            button = QRadioButton(size[0])
            button.setEnabled(False)
            if not first_button_is_checked:
                button.setChecked(True)
                first_button_is_checked = True
            self.window_size_layout.addWidget(button)

        self.group = QGroupBox('Window Size')
        self.group.setLayout(self.window_size_layout)
