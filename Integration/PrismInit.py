import os
import sys
PRISMROOT = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir, os.pardir)

prismRoot = os.getenv("PRISM_ROOT")
if not prismRoot:
    prismRoot = PRISMROOT

scriptDir = os.path.join(prismRoot, "Scripts")

if scriptDir not in sys.path:
    sys.path.append(scriptDir)
    sys.path.append(os.path.join(prismRoot, "PythonLibs/Python37/PySide"))

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismCore import PrismCore

def create(prismArgs=None):
    prismArgs = prismArgs or []

    qapp = QApplication.instance()
    if not qapp:
        qapp = QApplication(sys.argv)

    from UserInterfacesPrism import qdarkstyle
    qapp.setStyleSheet(qdarkstyle.load_stylesheet(pyside=True))
    iconPath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "UserInterfacesPrism",
        "p_tray.png",
    )
    appIcon = QIcon(iconPath)
    qapp.setWindowIcon(appIcon)
    pc = PrismCore(app="UnrealEngine", prismArgs=prismArgs)
    qapp.exec_()
    return pc

if __name__ == "__main__":
    create()