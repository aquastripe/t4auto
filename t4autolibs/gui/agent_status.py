from PySide6.QtWidgets import QLabel


class AgentStatus(QLabel):

    def __init__(self):
        super().__init__()

    def set_logged_in_status(self):
        self.setText('• Logged in')
        self.setStyleSheet('color: green;')

    def set_not_logged_in_status(self):
        self.setText('• Not logged in')
        self.setStyleSheet('color: red;')

    def set_running_status(self):
        self.setText('• Running')
        self.setStyleSheet('color: blue;')
