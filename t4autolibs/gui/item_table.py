import datetime
from enum import IntEnum
from threading import Thread

from PySide6 import QtGui
from PySide6.QtCore import Slot, QTime, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QGridLayout, QGroupBox, QTableWidget, QPushButton, QHeaderView, QTableWidgetItem, \
    QTimeEdit, QMenu

from t4autolibs.cores import ActionRow, ActionType

COLUMN_NAMES = ['Location', 'Search item by keyword', 'Start time', 'End time', 'Reason', 'Delete the row']


class ColumnIdx(IntEnum):
    LOCATION = 0
    KEYWORD = 1
    START = 2
    END = 3
    REASON = 4
    DELETE = 5


class ItemTable:

    def __init__(self, agent):
        self.agent = agent

        # Take items offline group
        self.layout = QGridLayout()
        self.group = QGroupBox('Take items offline')
        self.group.setLayout(self.layout)

        # Take items offline group / table
        self.table = QTableWidget()
        self.draw_table_header()
        self.table.cellClicked.connect(self.show_location)
        self.add_row()
        self.layout.addWidget(self.table, 0, 0, 1, 3)

        self.add_row_button = QPushButton('Add a row')
        self.add_row_button.setIcon(QtGui.QIcon('icons/add_box_FILL0_wght400_GRAD0_opsz24.svg'))
        self.add_row_button.clicked.connect(self.add_row)
        self.layout.addWidget(self.add_row_button, 1, 0)

        self.start_automation_button = QPushButton('Start taking items offline')
        self.start_automation_button.setIcon(QtGui.QIcon('icons/play_circle_FILL0_wght400_GRAD0_opsz24.svg'))
        self.start_automation_button.clicked.connect(self.start_automation)
        self.layout.addWidget(self.start_automation_button, 1, 1)

        self.stop_automation_button = QPushButton('Stop')
        self.stop_automation_button.setIcon(QtGui.QIcon('icons/stop_circle_FILL0_wght400_GRAD0_opsz24.svg'))
        self.stop_automation_button.clicked.connect(self.stop_automation)
        self.stop_automation_button.setEnabled(False)
        self.layout.addWidget(self.stop_automation_button, 1, 2)

    def show_location(self, row, column):
        if column != 0:
            return

        menu = QMenu()
        for store in self.agent.stores:
            action = QAction(store.name)
            action.triggered.connect(lambda: self.edit_location(row, column, store))
            menu.addAction(action)

        cell_rect = self.table.visualItemRect(self.table.item(row, column))
        global_position = self.table.viewport().mapToGlobal(cell_rect.bottomLeft())
        action = menu.exec(global_position)

    def edit_location(self, row, column, store):
        item = self.table.item(row, column)
        if item:
            item.setText(store.name)
            item.setData(Qt.UserRole, store)

    def draw_table_header(self):
        self.table.setColumnCount(len(COLUMN_NAMES))
        self.table.setHorizontalHeaderLabels(COLUMN_NAMES)
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

        self.table.setItem(row_idx, ColumnIdx.LOCATION, QTableWidgetItem(''))

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

    @Slot()
    def del_row(self):
        self.table.removeRow(self.table.currentRow())

    @Slot()
    def start_automation(self):
        self.start_automation_button.setEnabled(False)
        item_row_list = self.collect_items_from_table()
        if len(item_row_list) > 0:
            thread = Thread(target=self.agent.update_rules_loop, args=(item_row_list,))
            thread.start()
            self.stop_automation_button.setEnabled(True)
        else:
            self.start_automation_button.setEnabled(True)

    @Slot()
    def stop_automation(self):
        self.stop_automation_button.setEnabled(False)
        self.agent.stop()
        self.start_automation_button.setEnabled(True)

    def collect_items_from_table(self):
        item_row_list = []
        now = datetime.datetime.now()
        i = 0
        for row_idx in range(self.table.rowCount()):
            if self.table.item(row_idx, ColumnIdx.KEYWORD):
                keyword = self.table.item(row_idx, ColumnIdx.KEYWORD).text()
            else:
                continue

            start_time = self.table.cellWidget(row_idx, ColumnIdx.START).time().toPython()  # type: datetime.time
            start_datetime = now.replace(hour=start_time.hour, minute=start_time.minute, second=start_time.second)
            end_time = self.table.cellWidget(row_idx, ColumnIdx.END).time().toPython()  # type: datetime.time
            end_datetime = now.replace(hour=end_time.hour, minute=end_time.minute, second=end_time.second)

            if not self.table.item(row_idx, ColumnIdx.LOCATION):
                raise ValueError('Location does not selected.')

            store_id = self.table.item(row_idx, ColumnIdx.LOCATION).data(Qt.UserRole).id
            reason = self.table.item(row_idx, ColumnIdx.REASON).text() \
                if self.table.item(row_idx, ColumnIdx.REASON) else ''

            item_row = ActionRow(
                action_idx=i,
                keyword=keyword,
                action_time=start_datetime,
                action_type=ActionType.START,
                reason=reason,
                store_id=store_id,
            )
            item_row_list.append(item_row)
            item_row = ActionRow(
                action_idx=i,
                keyword=keyword,
                action_time=end_datetime,
                action_type=ActionType.END,
                reason=reason,
                store_id=store_id,
            )
            item_row_list.append(item_row)
            i += 1

        return item_row_list
