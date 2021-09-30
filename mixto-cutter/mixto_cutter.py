import cutter
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from urllib.error import HTTPError
from json import loads, dumps
from pathlib import Path
from PySide2.QtWidgets import (
    QLabel,
    QAction,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MixtoDockWidget(cutter.CutterDockWidget):
    def __init__(self, parent, action):
        super(MixtoDockWidget, self).__init__(parent, action)
        self.setObjectName("MixtoDockWidget")
        self.setWindowTitle("Mixto")
        self.mixto_entry_id = None
        self.command = ""
        self.main = parent

        conf_path = str(Path().home() / ".mixto.json")
        with open(conf_path) as f:
            mixto = loads(f.read())
            self.mixto_api = mixto.get("api_key")
            self.mixto_host = mixto.get("host")
            self.workspace = mixto.get("workspace")

        msg = "Unavailable"
        if self.mixto_api is None:
            self.mixto_api = msg
        if self.mixto_host is None:
            self.mixto_host = msg

        content = QWidget()
        self.setWidget(content)

        # Create layout and label
        layout = QVBoxLayout(content)
        content.setLayout(layout)
        self.text = QLabel(content)
        self.text.setText(
            "Host: {}\nAPI Key: {}\n".format(self.mixto_host, self.mixto_api)
        )
        # self.text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.text.setFont(cutter.Configuration.instance().getFont())
        layout.addWidget(self.text)

        self.inp_label = QLabel("Entry ID:")
        layout.addWidget(self.inp_label)
        self.input_eid = QLineEdit()
        self.input_eid.setMaximumWidth(200)
        layout.addWidget(self.input_eid)
        self.input_eid.textChanged.connect(self.get_eid)

        self.r2_command = QLabel("Radare command: ")
        layout.addWidget(self.r2_command)
        self.r2_cmd_inp = QLineEdit()
        self.r2_cmd_inp.setMaximumWidth(200)
        layout.addWidget(self.r2_cmd_inp)
        self.r2_cmd_inp.textChanged.connect(self.get_r2_cmd_inp)

        self.message = QLabel(content)
        # self.message.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # self.message.setFont(cutter.Configuration.instance().getFont())
        layout.addWidget(self.message)

        button = QPushButton(content)
        button.setText("Send to Mixto")
        # button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        button.setMaximumHeight(50)
        button.setMaximumWidth(200)
        layout.addWidget(button)
        # layout.setAlignment(button, Qt.AlignHCenter)

        button.clicked.connect(self.send_to_mixto)

        self.setupActions()

        self.show()

    def setupActions(self):
        self.decompileContext = QAction("Mixto - decompile", self)
        self.commentContext = QAction("Mixto - comments", self)
        menu = self.main.getContextMenuExtensions(cutter.MainWindow.ContextMenuType.Disassembly)
        menu.addAction(self.decompileContext)
        menu.addAction(self.commentContext)
        self.decompileContext.triggered.connect(self.sendDecompile)
        self.commentContext.triggered.connect(self.sendComments)

    def sendDecompile(self):
        self.command = 'pdg'
        self.send_to_mixto()

    def sendComments(self):
        self.command = 'af; CCf'
        self.send_to_mixto()

    def get_eid(self, text):
        self.mixto_entry_id = text

    def get_r2_cmd_inp(self, text):
        self.command = text

    def send_to_mixto(self):
        if self.mixto_entry_id is not None:
            arg = self.command[0:70]
            out = cutter.cmd(self.command).strip()
            url = urljoin(
                self.mixto_host, "/api/entry/" + self.workspace + "/" + self.mixto_entry_id + "/commit"
            )
            req = Request(
                method="POST",
                url=url,
                data=dumps(
                    {
                        "type": "tool",
                        "title": "(Cutter) - " + arg,
                        "data": out,
                        "meta": {},
                    }
                ).encode(),
                headers={
                    "x-api-key": self.mixto_api,
                    "Content-Type": "application/json",
                },
            )
            try:
                res = urlopen(req)
                status = res.getcode()
                if status > 300:
                    self.message.setText("{} error".format(status))
                else:
                    self.message.setText("OK!")
            except HTTPError as e:
                self.message.setText(getattr(e, "message", repr(e)))
        else:
            self.message.setText("Entry ID not provided")


class MixtoCutter(cutter.CutterPlugin):
    name = "mixto-cutter"
    description = "Cutter plugin for mixto"
    version = "1.0"
    author = "Hapsida @securisec"

    def setupPlugin(self):
        pass

    def setupInterface(self, main):
        action = QAction("Mixto", main)
        action.setCheckable(True)
        widget = MixtoDockWidget(main, action)
        main.addPluginDockWidget(widget, action)

    def terminate(self):
        pass


def create_cutter_plugin():
    try:
        return MixtoCutter()
    except Exception as e:
        print(e)
