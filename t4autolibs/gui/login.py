from PySide6 import QtGui
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QHBoxLayout, QCheckBox, QPushButton, QLabel

from t4autolibs.cores import UserInfo, LoginStatus, AgentV2
from t4autolibs.gui.agent_status import AgentStatus
from t4autolibs.gui.item_table import ItemTable


class Login:

    def __init__(self, agent: AgentV2, item_table: ItemTable, agent_status: AgentStatus):
        self.agent = agent
        self.item_table = item_table
        self.agent_status = agent_status

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
        self.checkbox_layout.addWidget(self.logout_button)

        self.layout.addRow(self.checkbox_layout)

        self.login_message = QLabel('')
        self.layout.addRow(self.login_message)

        self.set_logout_state()

    @Slot(int)
    def show_password(self, state):
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        elif Qt.CheckState(state) == Qt.CheckState.Unchecked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    @Slot()
    def login(self):
        if not self._is_logged_in:
            user_info = UserInfo(self.username_edit.text(), self.password_edit.text())
            login_status = self.agent.login(user_info)  # type: LoginStatus

            if login_status.success:
                self._is_logged_in = True
                self.set_login_state()
                self.login_message.setStyleSheet('color: green')
            else:
                self._is_logged_in = False
                self.set_logout_state()
                self.login_message.setStyleSheet('color: red')
            self.login_message.setText(login_status.message)

    @Slot()
    def logout(self):
        self.set_logout_state()
        if self._is_logged_in:
            login_status = self.agent.logout()  # type:LoginStatus

            if login_status.success:
                self._is_logged_in = False
                self.set_logout_state()
                self.login_message.setStyleSheet('color: green')
            else:
                self.login_message.setStyleSheet('color: red')
            self.login_message.setText(login_status.message)

    def set_logout_state(self):
        self.login_button.setEnabled(True)
        self.logout_button.setEnabled(False)
        self.username_edit.setEnabled(True)
        self.password_edit.setEnabled(True)
        self.display_password.setEnabled(True)

        self.item_table.set_initial_state()
        self.agent_status.set_not_logged_in_status()

    def set_login_state(self):
        self.login_button.setEnabled(False)
        self.logout_button.setEnabled(True)
        self.username_edit.setEnabled(False)
        self.password_edit.setEnabled(False)
        self.display_password.setEnabled(False)

        self.item_table.set_ready_state()
        self.agent_status.set_logged_in_status()
