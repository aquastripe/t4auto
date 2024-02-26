import sys
from enum import IntEnum

from PySide6 import QtGui
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QApplication, QGroupBox, QWidget, QLineEdit, QGridLayout, \
    QTableWidget, QFormLayout, QPushButton, QHeaderView, QDateTimeEdit, QVBoxLayout, QRadioButton, QCheckBox


class ColumnIdx(IntEnum):
    LOCATION = 0
    SEARCH = 1
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

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.display_password = QCheckBox('Show password')
        self.display_password.stateChanged.connect(self.show_password)

        self.login_layout.addRow('Username', self.username_edit)
        self.login_layout.addRow('Password', self.password_edit)
        self.login_layout.addWidget(self.display_password)

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

        self.table = QTableWidget()
        self.draw_table_header()
        self.add_a_row()
        self.take_offline_layout.addWidget(self.table, 0, 0, 1, 3)

        self.add_row_button = QPushButton('Add a row')
        self.add_row_button.setIcon(QtGui.QIcon('icons/add_box_FILL0_wght400_GRAD0_opsz24.svg'))
        self.add_row_button.clicked.connect(self.add_a_row)
        self.take_offline_layout.addWidget(self.add_row_button, 1, 0)
        self.start_automation = QPushButton('Start taking items offline')
        self.start_automation.setIcon(QtGui.QIcon('icons/play_circle_FILL0_wght400_GRAD0_opsz24.svg'))
        self.take_offline_layout.addWidget(self.start_automation, 1, 1)
        self.stop_automation = QPushButton('Stop')
        self.stop_automation.setIcon(QtGui.QIcon('icons/stop_circle_FILL0_wght400_GRAD0_opsz24.svg'))
        self.take_offline_layout.addWidget(self.stop_automation, 1, 2)

        # Compose all groups
        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.login_group, 0, 0)
        self.main_layout.addWidget(self.browser_group, 0, 1)
        self.main_layout.addWidget(self.take_offline_group, 1, 0, 1, 2)
        self.setLayout(self.main_layout)

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
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.SEARCH, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.START, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.END, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.REASON, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(ColumnIdx.DELETE, QHeaderView.ResizeMode.ResizeToContents)

    @Slot()
    def add_a_row(self):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        start_time = QDateTimeEdit()
        start_time.setDisplayFormat('hh:mm')
        start_time.setFrame(False)
        self.table.setCellWidget(row_idx, ColumnIdx.START, start_time)

        end_time = QDateTimeEdit()
        end_time.setDisplayFormat('hh:mm')
        end_time.setFrame(False)
        self.table.setCellWidget(row_idx, ColumnIdx.END, end_time)

        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(self.del_a_row)
        self.table.setCellWidget(row_idx, ColumnIdx.DELETE, delete_button)

    @Slot()
    def del_a_row(self):
        self.table.removeRow(self.table.currentRow())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('T4 Auto')
    t4auto_gui = T4AutoGUI()
    t4auto_gui.resize(800, 600)
    t4auto_gui.show()
    app.exec()


if __name__ == '__main__':
    main()
