from PySide6 import QtGui
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QHBoxLayout, QCheckBox, QPushButton, QVBoxLayout, \
    QRadioButton

from take_items_offline import UserInfo, LoginStatus


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
        self.login_button.setIcon(QtGui.QIcon('icons/login_24dp_FILL0_wght400_GRAD0_opsz24.svg'))
        self.login_button.clicked.connect(self.login)
        self.checkbox_layout.addWidget(self.login_button)

        self.logout_button = QPushButton('Logout')
        self.logout_button.setIcon(QtGui.QIcon('icons/logout_24dp_FILL0_wght400_GRAD0_opsz24.svg'))
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


class Browser:

    def __init__(self):
        self.browser_layout = QVBoxLayout()

        chrome_button = QRadioButton('Chrome')
        chrome_button.click()
        chrome_button.setEnabled(False)  # TODO: future feature
        self.browser_layout.addWidget(chrome_button)

        edge_button = QRadioButton('Edge')
        edge_button.setEnabled(False)
        self.browser_layout.addWidget(edge_button)

        firefox_button = QRadioButton('Firefox')
        firefox_button.setEnabled(False)
        self.browser_layout.addWidget(firefox_button)

        self.group = QGroupBox('Browser')
        self.group.setLayout(self.browser_layout)
