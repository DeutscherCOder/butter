
import clutter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget, QSizePolicy, QPushButton


class FortuneWidget(clutter.ClutterDockWidget):
    def __init__(self, parent):
        super(FortuneWidget, self).__init__(parent)
        self.setObjectName("FancyDockWidgetFromCoolPlugin")
        self.setWindowTitle("Sample Python Plugin")

        content = QWidget()
        self.setWidget(content)

        # Create layout and label
        layout = QVBoxLayout(content)
        content.setLayout(layout)
        self.text = QLabel(content)
        self.text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout.addWidget(self.text)

        button = QPushButton(content)
        button.setText("Want a fortune?")
        button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        button.setMaximumHeight(50)
        button.setMaximumWidth(200)
        layout.addWidget(button)
        layout.setAlignment(button, Qt.AlignHCenter)

        button.clicked.connect(self.generate_fortune)
        clutter.core().seekChanged.connect(self.generate_fortune)

        self.show()

    def generate_fortune(self):
        fortune = clutter.cmd("fortune").replace("\n", "")
        res = clutter.core().cmdRaw(f"?E {fortune}")
        self.text.setText(res)


class ClutterSamplePlugin(clutter.ClutterPlugin):
    name = "Sample Plugin"
    description = "A sample plugin written in python."
    version = "1.2"
    author = "Clutter developers"

    # Override ClutterPlugin methods

    def __init__(self):
        super(ClutterSamplePlugin, self).__init__()
        self.disassembly_actions = []
        self.addressable_item_actions = []
        self.disas_action = None
        self.addr_submenu = None
        self.main = None

    def setupPlugin(self):
        pass

    def setupInterface(self, main):
        # Dock widget
        widget = FortuneWidget(main)
        main.addPluginDockWidget(widget)

        # Dissassembly context menu
        menu = main.getContextMenuExtensions(clutter.MainWindow.ContextMenuType.Disassembly)
        self.disas_action = menu.addAction("ClutterSamplePlugin dissassembly action")
        self.disas_action.triggered.connect(self.handle_disassembler_action)
        self.main = main

        # Context menu for tables with addressable items like Flags,Functions,Strings,Search results,...
        addressable_item_menu = main.getContextMenuExtensions(clutter.MainWindow.ContextMenuType.Addressable)
        self.addr_submenu = addressable_item_menu.addMenu("ClutterSamplePlugin") # create submenu
        adrr_action = self.addr_submenu.addAction("Action 1")
        self.addr_submenu.addSeparator() # can use separator and other qt functionality
        adrr_action2 = self.addr_submenu.addAction("Action 2")
        adrr_action.triggered.connect(self.handle_addressable_item_action)
        adrr_action2.triggered.connect(self.handle_addressable_item_action)

    def terminate(self): # optional
        print("ClutterSamplePlugin shutting down")
        if self.main:
            menu = self.main.getContextMenuExtensions(clutter.MainWindow.ContextMenuType.Disassembly)
            menu.removeAction(self.disas_action)
            addressable_item_menu = self.main.getContextMenuExtensions(clutter.MainWindow.ContextMenuType.Addressable)
            submenu_action = self.addr_submenu.menuAction()
            addressable_item_menu.removeAction(submenu_action)
        print("ClutterSamplePlugin finished clean up")

    # Plugin methods

    def handle_addressable_item_action(self):
        # for actions in plugin menu Clutter sets data to current item address
        submenu_action = self.addr_submenu.menuAction()
        clutter.message("Context menu action callback 0x{:x}".format(submenu_action.data()))

    def handle_disassembler_action(self):
        # for actions in plugin menu Clutter sets data to address for current dissasembly line
        clutter.message("Dissasembly menu action callback 0x{:x}".format(self.disas_action.data()))


# This function will be called by Clutter and should return an instance of the plugin.
def create_clutter_plugin():
    return ClutterSamplePlugin()
