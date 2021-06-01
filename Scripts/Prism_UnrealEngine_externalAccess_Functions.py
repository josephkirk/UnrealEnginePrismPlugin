# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2020 Richard Frangenberg
#
# Licensed under GNU GPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.


from asyncio.log import logger
import os
import platform

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class Prism_UnrealEngine_externalAccess_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.callbacks = []
        # self.registerCallbacks()
        self._editorpath = ""
        self._projectpath = ""

    @property
    def editor(self):
        return self._editorpath

    @property
    def project(self):
        return self._projectpath

    @err_catcher(name=__name__)
    def setEditorPath(self, value):
        self._editorpath = value

    @err_catcher(name=__name__)
    def setProjectPath(self, value):
        self._projectpath = value

    @err_catcher(name=__name__)
    def registerCallbacks(self):
        self.callbacks.append(self.core.registerCallback("prismSettings_loadUI", self.prismSettings_loadUI))

    @err_catcher(name=__name__)
    def getAutobackPath(self, origin, tab):
        autobackpath = ""
        fileStr = "Unreal Engine Scene File ("
        for i in self.sceneFormats:
            fileStr += "*%s " % i

        fileStr += ")"

        return autobackpath, fileStr

    @err_catcher(name=__name__)
    def projectBrowser_loadUI(self, origin):
        if self.core.appPlugin.pluginName == "Standalone":
            psMenu = QMenu("Unreal Engine")
            psAction = QAction("Connect", origin)
            psAction.triggered.connect(lambda: self.connectToUnrealEngine(origin))
            psMenu.addAction(psAction)
            origin.menuTools.insertSeparator(origin.menuTools.actions()[-2])
            origin.menuTools.insertMenu(origin.menuTools.actions()[-2], psMenu)

    @err_catcher(name=__name__)
    def resolvePath(self, filepath):
        filepath = self.core.fixPath(filepath)
        result = self.core.callback(name="sc_resolvePath", types=["custom", "prjManagers"], args=[self, filepath], **{"as_depot_file": True})
        filepath = result if result else filepath

    @err_catcher(name=__name__)
    def browse(self, origin, getFile=False, windowTitle="Browse", fStr="All files (*)", uiEdit=None, subscribe_callable=None):
        browse_dir = getattr(uiEdit, "text", lambda : "")()
        if getFile:
            selectedPath = QFileDialog.getOpenFileName(
                    origin, windowTitle, browse_dir, fStr
                )[0]
        else:
            selectedPath = QFolderDialog.getExistingDirectory(
                    origin, windowTitle, browse_dir
                )[0]

        if getattr(uiEdit, "setText"):
            uiEdit.setText(self.resolvePath(selectedPath))
        if subscribe_callable:
            try:
                subscribe_callable(self.resolvePath(selectedPath))
            except Exception as why:
                logger.error(why)


    @err_catcher(name=__name__)
    def prismSettings_loadUI(self, origin, tab=None):

        w_ue4edior = QWidget()
        w_ue4edior.setLayout(QHBoxLayout())
        l_ue4editor = QLabel("UE4 editor path")
        origin.le_ue4editor = QLineEdit()
        origin.le_ue4editor.setText(self.editor)
        b_ue4editor = QPushButton("...")
        w_ue4edior.layout().addWidget(l_ue4editor)
        w_ue4edior.layout().addWidget(origin.le_ue4editor)
        w_ue4edior.layout().addWidget(b_ue4editor)

        w_ue4project = QWidget()
        w_ue4project.setLayout(QHBoxLayout())
        l_ue4project = QLabel("UE4 project path")
        origin.le_ue4project = QLineEdit()
        origin.le_ue4project.setText(self.project)
        b_ue4project = QPushButton("...")
        w_ue4project.layout().addWidget(l_ue4project)
        w_ue4project.layout().addWidget(origin.le_ue4project)
        w_ue4project.layout().addWidget(b_ue4project)
        
        # tab.layout().addWidget(w_ue4edior)
        tab.layout().addWidget(w_ue4project)

        origin.le_ue4editor.editingFinished.connect(self.setEditorPath)
        origin.le_ue4project.editingFinished.connect(self.setProjectPath)

        b_ue4editor.clicked.connect(lambda : self.browse(origin, True, "Select UE4-Editor.exe", "Executable (*.exe)", origin.le_ue4editor, self.setEditorPath))
        b_ue4project.clicked.connect(lambda : self.browse(origin, True, "Select Uproject file", "Uproject (*.uproject)", origin.le_ue4project, self.setProjectPath))

        return ""

    @err_catcher(name=__name__)
    def prismSettings_savePrjSettings(self, origin, settings):
        if "unrealengine" not in settings:
            settings["unrealengine"] = {}
        if hasattr(origin, "le_ue4editor"):
            settings["unrealengine"]["editor"] = self.editor
        if hasattr(origin, "le_ue4project"):
            settings["unrealengine"]["uproject"] = self.project

    @err_catcher(name=__name__)
    def prismSettings_loadPrjSettings(self, origin, settings):
        if "unrealengine" in settings:
            if "uproject" in settings["unrealengine"]:
                self.setProjectPath(settings["unrealengine"]["uproject"])
            if "editor" in settings["unrealengine"]:
                self.setEditorPath(settings["unrealengine"]["editor"])

    @err_catcher(name=__name__)
    def customizeExecutable(self, origin, appPath, filepath):
        # self.connectToUnrealEngine(origin, filepath=filepath)
        fileStarted = False
        # if self.core.getConfig("nuke", "usenukex"):
        #     if appPath == "":
        #         if not hasattr(self, "nukePath"):
        #             self.getNukePath(origin)

        #         if self.nukePath is not None and os.path.exists(self.nukePath):
        #             appPath = self.nukePath
        #         else:
        #             QMessageBox.warning(
        #                 self.core.messageParent,
        #                 "Warning",
        #                 "Nuke executable doesn't exist:\n\n%s" % self.nukePath,
        #             )

        #     if appPath is not None and appPath != "":
        #         subprocess.Popen([appPath, "--nukex", self.core.fixPath(filepath)])
        #         fileStarted = True

        return False

    @err_catcher(name=__name__)
    def copySceneFile(self, origin, origFile, targetPath, mode="copy"):
        pass

    @err_catcher(name=__name__)
    def onProjectCreated(self, origin, projectPath, projectName):
        pass

    @err_catcher(name=__name__)
    def connectToUnrealEngine(self, origin, filepath=""):
        pass