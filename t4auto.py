import sys
from datetime import datetime
from enum import IntEnum

from PySide6 import QtGui
from PySide6.QtCore import Slot, Qt, QDate
from PySide6.QtWidgets import QApplication, QGroupBox, QWidget, QLineEdit, QGridLayout, \
    QTableWidget, QFormLayout, QPushButton, QHeaderView, QDateTimeEdit, QVBoxLayout, QRadioButton, QCheckBox, \
    QHBoxLayout

from take_items_offline import ItemRow, UserInfo, Agent


class ColumnIdx(IntEnum):
    LOCATION = 0
    KEYWORD = 1
    START = 2
    REASON = 3
    DELETE = 4


class T4AutoGUI(QWidget):
    COLUMN_NAMES = ['Location', 'Search item by keyword', 'Start time', 'Reason', 'Delete the row']

    # COLUMN_NAMES = ['Location', 'Search item by keyword', 'Start time', 'End time', 'Reason', 'Delete the row']

    def __init__(self):
        super().__init__()
        # Login group
        self.login_layout = QFormLayout()
        self.login_group = QGroupBox('Login info')
        self.login_group.setLayout(self.login_layout)

        # Login group / username, password
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_layout.addRow('Username', self.username_edit)
        self.login_layout.addRow('Password', self.password_edit)

        # Login group / save username, show password
        self.checkbox_layout = QHBoxLayout()
        self.save_username = QCheckBox('Save username')
        self.checkbox_layout.addWidget(self.save_username)
        self.display_password = QCheckBox('Show password')
        self.display_password.stateChanged.connect(self.show_password)
        self.checkbox_layout.addWidget(self.display_password)
        self.login_layout.addRow(self.checkbox_layout)

        # Browser group
        self.browser_layout = QVBoxLayout()
        first_radio_button = QRadioButton('Chrome')
        first_radio_button.click()
        self.browser_layout.addWidget(first_radio_button)
        self.browser_layout.addWidget(QRadioButton('Edge'))
        self.browser_layout.addWidget(QRadioButton('Firefox'))
        self.browser_group = QGroupBox('Browser')
        self.browser_group.setLayout(self.browser_layout)

        # Take items offline group
        self.row_serial_id = 0
        self.take_offline_layout = QGridLayout()
        self.take_offline_group = QGroupBox('Take items offline')
        self.take_offline_group.setLayout(self.take_offline_layout)

        # Take items offline group / table
        self.table = QTableWidget()
        self.draw_table_header()
        self.add_row()
        self.take_offline_layout.addWidget(self.table, 0, 0, 1, 3)

        self.add_row_button = QPushButton('Add a row')
        self.add_row_button.setIcon(QtGui.QIcon('icons/add_box_FILL0_wght400_GRAD0_opsz24.svg'))
        self.add_row_button.clicked.connect(self.add_row)
        self.take_offline_layout.addWidget(self.add_row_button, 1, 0)

        self.start_automation_button = QPushButton('Start taking items offline')
        self.start_automation_button.setIcon(QtGui.QIcon('icons/play_circle_FILL0_wght400_GRAD0_opsz24.svg'))
        self.start_automation_button.clicked.connect(self.start_automation)
        self.take_offline_layout.addWidget(self.start_automation_button, 1, 1)

        self.stop_automation_button = QPushButton('Stop')
        self.stop_automation_button.setIcon(QtGui.QIcon('icons/stop_circle_FILL0_wght400_GRAD0_opsz24.svg'))
        self.take_offline_layout.addWidget(self.stop_automation_button, 1, 2)

        # Compose all groups
        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.login_group, 0, 0)
        self.main_layout.addWidget(self.browser_group, 0, 1)
        self.main_layout.addWidget(self.take_offline_group, 1, 0, 1, 2)
        self.setLayout(self.main_layout)

        self.agent = Agent()

    @Slot(int)
    def show_password(self, state):
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        elif Qt.CheckState(state) == Qt.CheckState.Unchecked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def draw_table_header(self):
        self.table.setColumnCount(len(self.COLUMN_NAMES))
        self.table.setHorizontalHeaderLabels(self.COLUMN_NAMES)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.LOCATION, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.KEYWORD, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.START, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.REASON, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.DELETE, QHeaderView.ResizeMode.ResizeToContents)

    @Slot()
    def add_row(self):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        start_time = QDateTimeEdit(QDate.currentDate())
        start_time.setDisplayFormat('hh:mm')
        start_time.setFrame(False)
        self.table.setCellWidget(row_idx, ColumnIdx.START, start_time)

        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(self.del_row)
        self.table.setCellWidget(row_idx, ColumnIdx.DELETE, delete_button)

    @Slot()
    def del_row(self):
        self.table.removeRow(self.table.currentRow())

    @Slot()
    def start_automation(self):
        item_row_list = []
        for row_idx in range(self.table.rowCount()):
            start_time = self.table.cellWidget(row_idx, ColumnIdx.START).dateTime().toPython()  # type: datetime
            now = datetime.now()
            today = dict(
                year=now.year,
                month=now.month,
                day=now.day
            )
            start_time.replace(**today)
            location = self.table.item(row_idx, ColumnIdx.LOCATION).text() \
                if self.table.item(row_idx, ColumnIdx.LOCATION) else ''
            keyword = self.table.item(row_idx, ColumnIdx.KEYWORD).text() \
                if self.table.item(row_idx, ColumnIdx.KEYWORD) else ''
            reason = self.table.item(row_idx, ColumnIdx.REASON).text() \
                if self.table.item(row_idx, ColumnIdx.REASON) else ''
            item_row = ItemRow(
                location=location,
                keyword=keyword,
                start_time=start_time,
                reason=reason,
            )
            item_row_list.append(item_row)

        self.agent.create_browser_session()
        self.agent.login(UserInfo(self.username_edit.text(), self.password_edit.text()))
        self.agent.update_rules_loop(item_row_list)

    @Slot()
    def stop_automation(self):
        if self.agent.session_is_started:
            self.agent.stop()
            self.agent.destroy_browser_session()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('T4 Auto')
    t4auto_gui = T4AutoGUI()
    t4auto_gui.resize(800, 600)
    t4auto_gui.show()
    app.exec()


if __name__ == '__main__':
    main()
