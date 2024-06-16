from PySide6.QtWidgets import QMainWindow

from t4autolibs.gui.t4auto_gui import Composition


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.t4auto_gui = Composition(self)
        self.setCentralWidget(self.t4auto_gui)

        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().addPermanentWidget(self.t4auto_gui.agent_status)

    def load_config_from_file(self):
        self.t4auto_gui.load_config_from_file()

    def dump_config_to_file(self):
        self.t4auto_gui.dump_config_to_file()
