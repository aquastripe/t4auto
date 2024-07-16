import datetime
from enum import IntEnum
from typing import NoReturn

from PySide6 import QtGui
from PySide6.QtCore import Slot, QTime, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QGridLayout, QGroupBox, QTableWidget, QPushButton, QHeaderView, QTableWidgetItem, \
    QTimeEdit, QMenu

from t4autolibs.cores import ActionRowV2, ActionType, Store, AgentV2
from t4autolibs.gui.agent_status import AgentStatus
from t4autolibs.gui.config import Configurable

COLUMN_NAMES = ['Location', 'Search items by keyword', 'Offline time', 'Online time', 'Reason', 'Delete the row']


class ColumnIdx(IntEnum):
    LOCATION = 0
    KEYWORD = 1
    START = 2
    END = 3
    REASON = 4
    DELETE = 5


class ItemTable(Configurable):

    def __init__(self, agent: AgentV2, agent_status: AgentStatus):
        self.agent = agent
        self.agent_status = agent_status

        # Take items offline group
        self.layout = QGridLayout()
        self.group = QGroupBox('Take items offline')
        self.group.setLayout(self.layout)

        # Take items offline group / table
        self.table = QTableWidget()
        self.draw_table_header()
        self.table.cellClicked.connect(self.show_location)
        self.layout.addWidget(self.table, 0, 0, 1, 3)

        self.add_row_button = QPushButton('Add a row')
        self.add_row_button.setIcon(QtGui.QIcon('_internal/icons/add.svg'))
        self.add_row_button.clicked.connect(self.add_empty_row)
        self.layout.addWidget(self.add_row_button, 1, 0)

        self.start_automation_button = QPushButton('Start taking items offline')
        self.start_automation_button.setIcon(QtGui.QIcon('_internal/icons/play.svg'))
        self.start_automation_button.clicked.connect(self.start_automation)
        self.layout.addWidget(self.start_automation_button, 1, 1)

        self.stop_automation_button = QPushButton('Stop')
        self.stop_automation_button.setIcon(QtGui.QIcon('_internal/icons/stop.svg'))
        self.stop_automation_button.clicked.connect(self.stop_automation)
        self.layout.addWidget(self.stop_automation_button, 1, 2)

        self.set_initial_state()

    def set_initial_state(self):
        for table_widget in self.group.findChildren(QTableWidget):  # type: QTableWidget
            table_widget.setEnabled(False)

        self.add_row_button.setEnabled(False)
        self.start_automation_button.setEnabled(False)
        self.stop_automation_button.setEnabled(False)

    def set_ready_state(self):
        for table_widget in self.group.findChildren(QTableWidget):  # type: QTableWidget
            table_widget.setEnabled(True)

        self.add_row_button.setEnabled(True)
        self.start_automation_button.setEnabled(True)
        self.stop_automation_button.setEnabled(False)

    def set_running_state(self):
        for table_widget in self.group.findChildren(QTableWidget):  # type: QTableWidget
            table_widget.setEnabled(False)

        self.add_row_button.setEnabled(False)
        self.start_automation_button.setEnabled(False)
        self.stop_automation_button.setEnabled(True)
        self.agent_status.set_running_status()

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
    def add_empty_row(self):
        row_idx = self.table.rowCount()
        store = {
            'id': -1,
            'name': '',
        }
        self.add_row(row_idx, store, '', (0, 0), (23, 59), '')

    def add_row(self, row_idx: int, store: dict, keyword: str, start_time: tuple[int, int], end_time: tuple[int, int],
                reason: str):
        self.table.insertRow(row_idx)

        store = Store(store['id'], store['name'])
        store_item = QTableWidgetItem(store.name)
        store_item.setData(Qt.UserRole, store)
        self.table.setItem(row_idx, ColumnIdx.LOCATION, store_item)

        keyword_item = QTableWidgetItem(keyword)
        self.table.setItem(row_idx, ColumnIdx.KEYWORD, keyword_item)

        start_time_edit = QTimeEdit(QTime(*start_time))
        start_time_edit.setDisplayFormat('hh:mm')
        start_time_edit.setFrame(False)
        self.table.setCellWidget(row_idx, ColumnIdx.START, start_time_edit)

        end_time_edit = QTimeEdit(QTime(*end_time))
        end_time_edit.setDisplayFormat('hh:mm')
        end_time_edit.setFrame(False)
        self.table.setCellWidget(row_idx, ColumnIdx.END, end_time_edit)

        reason_edit = QTableWidgetItem(reason)
        self.table.setItem(row_idx, ColumnIdx.REASON, reason_edit)

        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(self.del_row)
        self.table.setCellWidget(row_idx, ColumnIdx.DELETE, delete_button)

    @Slot()
    def del_row(self):
        self.table.removeRow(self.table.currentRow())

    @Slot()
    def start_automation(self):
        self.start_automation_button.setEnabled(False)
        self.stop_automation_button.setEnabled(True)
        self.agent_status.set_running_status()

        action_row_list = self.collect_action_rows_from_table()
        if len(action_row_list) > 0:
            self.agent.start_scheduler(action_row_list)
        else:
            self.start_automation_button.setEnabled(True)
            self.stop_automation_button.setEnabled(False)
            self.agent_status.set_logged_in_status()

    @Slot()
    def stop_automation(self):
        self.start_automation_button.setEnabled(True)
        self.stop_automation_button.setEnabled(False)
        self.agent_status.set_logged_in_status()
        self.agent.stop_scheduler()

    def collect_action_rows_from_table(self):
        action_row_list = []
        now = datetime.datetime.now()
        for row_idx in range(self.table.rowCount()):
            keyword = self.table.item(row_idx, ColumnIdx.KEYWORD).text()
            if keyword == '':
                # Keyword is not set; skipped.
                continue

            store = self.table.item(row_idx, ColumnIdx.LOCATION).data(Qt.UserRole)
            if store.id == -1:
                # Location is not set; skipped.
                continue

            start_time = self.table.cellWidget(row_idx, ColumnIdx.START).time().toPython()  # type: datetime.time
            start_datetime = now.replace(hour=start_time.hour, minute=start_time.minute, second=start_time.second)
            end_time = self.table.cellWidget(row_idx, ColumnIdx.END).time().toPython()  # type: datetime.time
            end_datetime = now.replace(hour=end_time.hour, minute=end_time.minute, second=end_time.second)
            reason = self.table.item(row_idx, ColumnIdx.REASON).text()

            item_row = ActionRowV2(
                keyword=keyword,
                action_time=start_datetime,
                action_type=ActionType.START,
                reason=reason,
                store_id=store.id,
            )
            action_row_list.append(item_row)
            item_row = ActionRowV2(
                keyword=keyword,
                action_time=end_datetime,
                action_type=ActionType.END,
                reason=reason,
                store_id=store.id,
            )
            action_row_list.append(item_row)

        return action_row_list

    def load_config(self, config: dict) -> NoReturn:
        if config['ItemTable'] is None:
            return

        for row in config['ItemTable']:
            self.add_row(
                row['row_idx'], row['store'], row['keyword'], row['start_time'], row['end_time'], row['reason']
            )

    def dump_config(self) -> dict:
        config = {
            'ItemTable': [],
        }
        for row_idx in range(self.table.rowCount()):
            row = {
                'row_idx': row_idx,
            }
            store = self.table.item(row_idx, ColumnIdx.LOCATION).data(Qt.UserRole)  # type: Store
            row['store'] = {
                'id': store.id,
                'name': store.name,
            }
            row['keyword'] = self.table.item(row_idx, ColumnIdx.KEYWORD).text() \
                if self.table.item(row_idx, ColumnIdx.KEYWORD) else ''

            start_time = self.table.cellWidget(row_idx, ColumnIdx.START).time().toPython()  # type: datetime.time
            row['start_time'] = (start_time.hour, start_time.minute)
            end_time = self.table.cellWidget(row_idx, ColumnIdx.END).time().toPython()  # type: datetime.time
            row['end_time'] = (end_time.hour, end_time.minute)
            reason = self.table.item(row_idx, ColumnIdx.REASON).text() \
                if self.table.item(row_idx, ColumnIdx.REASON) else ''
            row['reason'] = reason

            config['ItemTable'].append(row)

        return config
