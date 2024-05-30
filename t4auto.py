import datetime
import sys
from enum import IntEnum
from threading import Thread

from PySide6 import QtGui
from PySide6.QtCore import Slot, Qt, QTime
from PySide6.QtWidgets import QApplication, QGroupBox, QWidget, QLineEdit, QGridLayout, \
    QTableWidget, QFormLayout, QPushButton, QHeaderView, QVBoxLayout, QRadioButton, QCheckBox, \
    QHBoxLayout, QTimeEdit, QMenu, QTableWidgetItem

from take_items_offline import ActionRow, UserInfo, Agent, ActionType


class ColumnIdx(IntEnum):
    LOCATION = 0
    KEYWORD = 1
    START = 2
    END = 3
    REASON = 4
    DELETE = 5


class T4AutoGUI(QWidget):
    COLUMN_NAMES = ['Location', 'Search item by keyword', 'Start time', 'End time', 'Reason', 'Delete the row']

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

        self.login_layout.addRow(self.checkbox_layout)

        # Browser group
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
        self.table.cellClicked.connect(self._show_location)
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
        self.stop_automation_button.clicked.connect(self.stop_automation)
        self.stop_automation_button.setEnabled(False)
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
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.END, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.REASON, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.DELETE, QHeaderView.ResizeMode.ResizeToContents)

    @Slot()
    def add_row(self):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        self.table.setItem(row_idx, ColumnIdx.LOCATION, QTableWidgetItem('Location'))

        start_time = QTimeEdit(QTime(0, 0))
        start_time.setDisplayFormat('hh:mm')
        start_time.setFrame(False)
        self.table.setCellWidget(row_idx, ColumnIdx.START, start_time)

        end_time = QTimeEdit(QTime(23, 59))
        end_time.setDisplayFormat('hh:mm')
        end_time.setFrame(False)
        self.table.setCellWidget(row_idx, ColumnIdx.END, end_time)

        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(self.del_row)
        self.table.setCellWidget(row_idx, ColumnIdx.DELETE, delete_button)

    def _show_location(self, row, column):
        if column != 0:
            return

        menu = QMenu()

        location = menu.addAction('Location')

        cell_rect = self.table.visualItemRect(self.table.item(row, column))
        global_position = self.table.viewport().mapToGlobal(cell_rect.bottomLeft())
        action = menu.exec(global_position)

    @Slot()
    def del_row(self):
        self.table.removeRow(self.table.currentRow())

    @Slot()
    def login(self):
        self.login_button.setEnabled(False)
        self.logout_button.setEnabled(True)
        if not self._is_logged_in:
            self._is_logged_in = True
            user_info = UserInfo(self.username_edit.text(), self.password_edit.text())
            self.agent.login(user_info)

    @Slot()
    def logout(self):
        self.login_button.setEnabled(True)
        self.logout_button.setEnabled(False)
        if self._is_logged_in:
            self._is_logged_in = False
            self.agent.logout()

    @Slot()
    def start_automation(self):
        self.start_automation_button.setEnabled(False)
        item_row_list = self._collect_actions_from_table()
        if len(item_row_list) > 0:
            thread = Thread(target=self.agent.update_rules_loop, args=(item_row_list,))
            thread.start()
            self.stop_automation_button.setEnabled(True)
        else:
            self.start_automation_button.setEnabled(True)

    def _collect_actions_from_table(self):
        item_row_list = []
        now = datetime.datetime.now()
        i = 0
        for row_idx in range(self.table.rowCount()):
            if self.table.item(row_idx, ColumnIdx.KEYWORD):
                keyword = self.table.item(row_idx, ColumnIdx.KEYWORD).text()
            else:
                continue

            start_time = self.table.cellWidget(row_idx, ColumnIdx.START).time().toPython()  # type: datetime.time
            end_time = self.table.cellWidget(row_idx, ColumnIdx.END).time().toPython()  # type: datetime.time
            start_datetime = now.replace(hour=start_time.hour, minute=start_time.minute, second=start_time.second)
            end_datetime = now.replace(hour=end_time.hour, minute=end_time.minute, second=end_time.second)

            location = self.table.item(row_idx, ColumnIdx.LOCATION).text() \
                if self.table.item(row_idx, ColumnIdx.LOCATION) else ''
            reason = self.table.item(row_idx, ColumnIdx.REASON).text() \
                if self.table.item(row_idx, ColumnIdx.REASON) else ''

            item_row = ActionRow(
                action_idx=i,
                location=location,
                keyword=keyword,
                action_time=start_datetime,
                action_type=ActionType.START,
                reason=reason,
                store_id=int(sys.argv[1]),  # TODO: fetch store_id from API
            )
            item_row_list.append(item_row)
            item_row = ActionRow(
                action_idx=i,
                location=location,
                keyword=keyword,
                action_time=end_datetime,
                action_type=ActionType.END,
                reason=reason,
                store_id=int(sys.argv[1]),  # TODO: fetch store_id from API
            )
            item_row_list.append(item_row)
            i += 1

        return item_row_list

    @Slot()
    def stop_automation(self):
        self.stop_automation_button.setEnabled(False)
        if self.agent.session_is_started:
            self.agent.stop()
            self.agent.destroy_browser_session()
        self.start_automation_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('T4 Auto')
    t4auto_gui = T4AutoGUI()
    t4auto_gui.resize(800, 600)
    t4auto_gui.show()
    app.exec()


if __name__ == '__main__':
    main()
