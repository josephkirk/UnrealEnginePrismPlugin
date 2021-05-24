#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import os
import glob
from os.path import basename, dirname, splitext
from subprocess import Popen
import json
from functools import partial

def get_temp_path():
    p = os.path.join(os.getenv("TMP"), os.path.splitext(os.path.basename(__file__))[0])
    if not os.path.exists(p):
        os.makedirs(p)
    return p


class RenderOutputFormat(object):
    JPG = "jpg"
    BMP = "bmp"
    PNG = "png"
    Video = "video"

class ImportData(object):
    def __init__(self):
        # self.ImportTranslation= [0,0,0]
        # self.ImportRotation = [0,0,0]
        # self.ImportUniformScale = [1,1,1]
        self.bConvertScene = True
        self.bConvertSceneUnit = True
        self.bConvertAsScene = True

class StaticMeshImportData(ImportData):
    def __init__(self):
        ImportData.__init__(self)
        self.bRemoveDegenerates = True
        self.bBuildAdjacencyBuffer = True
        self.bBuildReversedIndexBuffer = False
        self.bGenerateLightmapUVs = False
        self.bOneConvexHullPerUCX = True
        self.bAutoGenerateCollision = False
        self.bCombineMeshes = False

class SkeletalMeshImportData(ImportData):
    TargetSkeleton = ""
    def __init__(self):
        ImportData.__init__(self)
        self.bUpdateSkeletonReferencePose = True
        self.bUseT0AsRefPose = True
        self.bPreserveSmoothingGroups = True
        self.bImportMeshesInBoneHierarchy = False
        self.bImportMorphTargets = True
        self.bKeepOverlappingVertices = True
    

class AnimSequenceImportData(ImportData):
    TargetSkeleton = ""
    def __init__(self):
        ImportData.__init__(self)
        self.bImportCustomAttribute = True
        self.bDeleteExistingCustomAttributeCurves = True
        self.bDeleteExistingNonCurveCustomAttributes = True
        self.bImportBoneTracks = True
        self.bSetMaterialDriveParameterOnCustomAttribute = True
        self.bRemoveRedundantKeys = False
        self.bDeleteExistingMorphTargetCurves = False
        self.bDoNotImportCurveWithZero = True
        self.bPreserveLocalTransform = False

class TextureImportData(ImportData):
    def __init__(self):
        self.bInvertNormalMaps = True

class FBXImportSettings(object):
    """
    ImportSettings in Setting Group is UFbxImportUI:
        bIsObjImport /** Whether or not the imported file is in OBJ format */
        OriginalImportType /** The original detected type of this import */
        MeshTypeToImport /** Type of asset to import from the FBX file */
        bOverrideFullName : true /** Use the string in "Name" field as full name of mesh. The option only works when the scene contains one mesh. */
        bImportAsSkeletal /** Whether to import the incoming FBX as a skeletal object */
        bImportMesh /** Whether to import the incoming FBX as a Subdivision Surface (could be made a combo box together with bImportAsSkeletal) (Experimental, Early work in progress) */
	                /** Whether to import the mesh. Allows animation only import when importing a skeletal mesh. */
        Skeleton /** Skeleton to use for imported asset. When importing a mesh, leaving this as "None" will create a new skeleton. When importing an animation this MUST be specified to import the asset. */
        bCreatePhysicsAsset /** If checked, create new PhysicsAsset if it doesn't have it */
        bAutoComputeLodDistances ** If checked, the editor will automatically compute screen size values for the static mesh's LODs. If unchecked, the user can enter custom screen size values for each LOD. */
        LodDistance0 /** Set a screen size value for LOD 0*/
        LodDistance1 /** Set a screen size value for LOD 1*/
        LodDistance2 /** Set a screen size value for LOD 2*/
        LodDistance3 /** Set a screen size value for LOD 3*/
        LodDistance4 /** Set a screen size value for LOD 4*/
        LodDistance5 /** Set a screen size value for LOD 5*/
        LodDistance6 /** Set a screen size value for LOD 6*/
        LodDistance7 /** Set a screen size value for LOD 7*/
        MinimumLodNumber /** Set the minimum LOD used for rendering. Setting the value to 0 will use the default value of LOD0. */
        LodNumber /** Set the number of LODs for the editor to import. Setting the value to 0 imports the number of LODs found in the file (up to the maximum). */
        bImportAnimations /** True to import animations from the FBX File */
        OverrideAnimationName /** Override for the name of the animation to import. By default, it will be the name of FBX **/
        bImportRigidMesh /** Enables importing of 'rigid skeletalmesh' (unskinned, hierarchy-based animation) from this FBX file, no longer shown, used behind the scenes */
        bImportMaterials /** If no existing materials are found, whether to automatically create Unreal materials for materials found in the FBX scene */
        bImportTextures /** Whether or not we should import textures. This option is disabled when we are importing materials because textures are always imported in that case. */
        bResetToFbxOnMaterialConflict /** If true, the imported material sections will automatically be reset to the imported data in case of a reimport conflict. */
        StaticMeshImportData /** Import data used when importing static meshes */
        SkeletalMeshImportData /** Import data used when importing skeletal meshes */
        AnimSequenceImportData /** Import data used when importing animations */
        TextureImportData /** Import data used when importing textures */
        bAutomatedImportShouldDetectType /** If true the automated import path should detect the import type.  If false the import type was specified by the user */
        bIsReimport
        bAllowContentTypeImport
    """
    def __init__(self):
        self.settings = dict(ImportGroups = [])
        self._groups = []

    def _add_group(self, setting_group):
        self.settings["ImportGroups"].append(setting_group)

    def addGroup(self, group_name, files_path, destination, import_setting, is_reimport=False):
        if not issubclass(import_setting.__class__, ImportData):
            print("import_setting input should be of class ImportSetting")
        setting_group = {
            "GroupName": group_name,
            "Filenames": files_path,
            "DestinationPath": destination,
            "bReplaceExisting": True,
            "bSkipReadOnly": True,
            "FactoryName": "FbxFactory",
            "ImportSettings": {}
        }
        raw_setting = vars(import_setting)
        if hasattr(import_setting, "TargetSkeleton"):
            setting_group["ImportSettings"]["Skeleton"] = str(import_setting.TargetSkeleton)
            raw_setting.pop("TargetSkeleton")
        if is_reimport:
            setting_group["ImportSettings"]["bIsReimport"] = True
        setting_group["ImportSettings"][import_setting.__class__.__name__] = raw_setting

        self._add_group(setting_group)
        return setting_group

    def getGroup(self, group_name):
        for setting in self.settings["ImportGroups"]:
            if setting["GroupName"] == group_name:
                return setting

    def asJson(self, filepath=""):
        if not filepath:
            import datetime
            filepath = os.path.join(os.getenv("TMP"), "UE4CMD", "importsetting.{}.json".format(datetime.datetime.now().strftime("%d%m%Y%H%M%S")))
            try:
                os.makedirs(os.path.dirname(filepath))
            except:
                pass
        try:
            with open(filepath, "w+") as f:
                json.dump(self.settings, f, sort_keys=True, indent=4, separators=(',', ': '))
        except:
            print("Failed to export setting as json")
        return filepath

class NoEditorException(Exception):
    pass

class NoProjectException(Exception):
    pass


class Unreal4Config(object):
    pass

class UserEngine(Unreal4Config):
    content = r"""
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
{}
bDeveloperMode=True
bRemoteExecution=True
RemoteExecutionMulticastGroupEndpoint={}
RemoteExecutionMulticastBindAddress={}
RemoteExecutionSendBufferSizeBytes={}
RemoteExecutionReceiveBufferSizeBytes={}
RemoteExecutionMulticastTtl=0
    """
    multicastendpoint = "239.0.0.1:6766"
    multicastbindaddress = "0.0.0.0"
    SendBufferSize = 2097152
    ReceiveBufferSize = 2097152
    def __init__(self):
        self.startupScript = ""
        self.AdditionalPaths = []

    def setStarupScript(self, startupscript_path):
        if os.path.exists(startupscript_path) and startupscript_path.endswith(".py"):
            self.startupScript = "+StartupScripts={}".format(startupscript_path)

    def addAdditionalPythonPath(self, python_path):
        if os.path.exists(python_path):
            self.AdditionalPaths.append(r"+AdditionalPaths=(Path=\"{}\")".format(python_path))

    def saveAsConfig(self, outputpath=""):
        script_path = []
        if self.startupScript:
            script_path.append(self.startupScript)
        if self.AdditionalPaths:
            script_path.extend(self.AdditionalPaths)
        script_path = "\n".join(script_path)
        content = self.content.format(script_path, self.multicastendpoint, self.multicastbindaddress, self.SendBufferSize, self.ReceiveBufferSize)
        config_path = outputpath
        if not config_path:
            config_path = os.path.join(get_temp_path(), "UserEngine.ini")
        with open(config_path, "w+") as f:
            f.write(content)
        return config_path

    @classmethod
    def asConfig(cls, outputpath=""):
        return cls().saveAsConfig(outputpath)

class Unreal4CMD(object):
    def __init__(self, editor="", project=""):
        self._editor = editor or os.getenv("UE4Editor", "")
        self._project = project or os.getenv("UE4Project", "")

    @property
    def editor(self):
        return str(self._editor)

    @editor.setter
    def editor(self, editor_path):
        self._editor = editor_path

    @property
    def project(self):
        return str(self._project)

    @project.setter
    def project(self, project_path):
        self._project = project_path

    def getCMD(self):
        if self.editor and os.path.exists(self.editor):
            if os.path.isfile(self.editor) and os.path.basename(self.editor) == "UE4Editor-Cmd.exe":
                return self.editor
            for r in glob.glob(os.path.normpath(self.editor) + "/Binaries/Win64/UE4Editor-Cmd.exe"):
                return r

    def getEditor(self):
        if self.editor and os.path.exists(self.editor):
            if os.path.isfile(self.editor) and os.path.basename(self.editor) == "UE4Editor.exe":
                return self.editor
            for r in (glob.glob(os.path.normpath(self.editor) + "/Binaries/Win64/UE4Editor.exe")):
                return r

    def getProject(self):
        if self.project and os.path.exists(self.project):
            if os.path.isfile(self.project) and self.project.endswith("*.uproject"):
                return self.project
            for r in glob.glob(self.project + "/*.uproject"):
                return r

    def getProjectConfig(self):
        projectfile_path = self.getProject()
        if projectfile_path:
            try:
                from StringIO import StringIO
                print(projectfile_path)
                data = str.decode(open(projectfile_path, 'r').read(), encoding='utf-8-sig')
                return json.loads(data)
            except Exception as why:
                print("Failed to parse project {} as json!\n{}".format(projectfile_path, why))
        else:
            raise NoProjectException("No valid file project!")

    def saveProjectConfig(self, project_config={}):
        if not project_config:
            project_config = self.getProjectConfig()
        projectfile_path = self.getProject()
        try:
            with open(projectfile_path, "w+") as f:
                json.dump(project_config, f, sort_keys=True, indent=4, separators=(',', ': '))
        except Exception as why:
            print(r"Cannot directly edit {} with error {}".format(os.path.basename(projectfile_path), why))
            projectfile_path = os.path.join(os.path.dirname(projectfile_path), "Edit{}".format(os.path.basename(projectfile_path)))
            with open(projectfile_path, "w+") as f:
                json.dump(project_config, f, sort_keys=True, indent=4, separators=(',', ': '))

    def setPlugins(self, projectfile_path, plugins):
        project_config = self.getProjectConfig()
        for plugin in plugins:
            for project_plugin in project_config["Plugins"]:
                if project_plugin.get("Name") == plugin.get("Name"):
                    project_plugin["Enabled"] = plugin.get("Enabled")
                    break
            else:
                project_config["Plugins"].append(plugin)
        self.saveProjectConfig(project_config)
        return projectfile_path


    def run_editor(
        self,
        map_path=None,
        argv= [],
        plugins = [
            {
                "Name": "PythonScriptPlugin",
                "Enabled": True
            },
            {
                "Name": "SequencerScripting",
                "Enabled": True
            },
            {
                "Name": "PythonAutomationTest",
                "Enabled": True
            },
            {
                "Name": "EditorScriptingUtilities",
                "Enabled": True
            }
        ],
        log= False,
        consolevariables= [],
        run_process_callable= Popen,
        custom_editor_path= "",
        custom_project_path= "",
        UserConfig = UserEngine.asConfig(),
        as_cmd= False,
        communicate = False
    ):
        getEditor = self.getCMD if as_cmd else self.getEditor
        editor_path = getEditor() or custom_editor_path
        if not editor_path:
            raise NoEditorException("No UE4 Editor Define")

        project_path = self.getProject() or custom_project_path
        if not project_path:
            raise NoEditorException("No Project Define")

        project_path = self.setPlugins(project_path, plugins)
    
        argv.append(r'-ExecCmds="{}"'.format(";".join(consolevariables)))
        if log:
            if isinstance(log, str):
                if os.path.split(log)[0]:
                    argv.append(r'ABSLOG="{}"'.format(log))
                else:
                    argv.append(r'LOG="{}"'.format(log))
            else:
                argv.append("-log")
        cmd = [editor_path, project_path]
        if map_path:
            cmd.append(map_path)
        if as_cmd:
            cmd.append("-silent")
            cmd.append("-UNATTENDED")
            cmd.append("-NOSPLASH")
            cmd.append("-NOLOADSTARTUPPACKAGES")
            cmd.append("-targetplatform=WindowsNoEditor")
        cmd.extend(argv)
        cmd.append("EDITORUSERSETTINGSINI={}".format(UserConfig))
        print("Run Unreal Editor with commands: {}".format(" ".join(cmd)))
        p = run_process_callable(cmd)
        if run_process_callable == Popen and communicate:
            p.communicate()
        return p

    def run_render(
        self,
        map_path,
        sequence_path,
        output_folder = "render",
        output_name = r"Render.{frame}",
        output_format= RenderOutputFormat.PNG,
        start_frame = 0,
        end_frame = 0,
        res_x = 1920,
        rex_y = 1080,
        frame_rate = 30,
        quality = 100,
        warmup_frames = 30,
        delay_frames = 30,
        delaybeforeshot_frames = 0,
        delayeveryframe_frames = 0,
        preview= False,
        shot=None,
        useburnin=False,
        write_editdecisionlist=None,
        write_finalcutxml=None,
        log=True
    ):
        cmds = [
            "-game",
            '-MovieSceneCaptureType="/Script/MovieSceneCapture.AutomatedLevelSequenceCapture"',
            '-LevelSequence="{}"'.format(sequence_path),
            "-NoLoadingScreen",
            "-ResX={}".format(res_x),
            "-ResY={}".format(rex_y),
            "-ForceRes",
            "-NoVSync" if preview else "-VSync",
            "-MovieFrameRate={}".format(frame_rate),
            "-NoTextureStreaming",
            "-MovieCinematicMode=Yes",
            "-MovieWarmUpFrames={}".format(warmup_frames),
            "-MovieDelayBeforeWarmUp={}".format(delay_frames),
            "-MovieDelayBeforeShotWarmUp={}".format(delaybeforeshot_frames),
            "-MovieDelayEveryFrame={}".format(delayeveryframe_frames),
            "-MovieQuality={}".format(quality),
            '-MovieFolder="{}"'.format(output_folder),
            '-MovieName="{}"'.format(output_name),
            '-MovieFormat="{}"'.format(output_format),
            '-UseBurnIn="{}"'.format(useburnin),
            "-NoScreenMessage",
            "-WINDOWED"
        ]
        if shot:
            cmds.append('-Shot="{}"'.format(shot))
        if start_frame:
            cmds.append("-MovieStartFrame={}".format(start_frame))
        if end_frame:
            cmds.append("-MovieEndFrame={}".format(end_frame))
        if write_editdecisionlist:
            cmds.append("-WriteEditDecisionList={}".format(write_editdecisionlist))
        if write_finalcutxml:
            cmds.append("-WriteFinalCutProXML={}".format(write_finalcutxml))

        console_commands = [
            "DisableAllScreenMessages",
            "r.DepthOfFieldQuality=4",
            "r.MotionBlurSeparable=1",
            "r.MotionBlurQuality=4"
        ]
        return self.run_editor(map_path= map_path, argv=cmds, consolevariables=console_commands, as_cmd=True, log=log, communicate=True)

    def run_python(
        self,
        python_file,
        fully_initialize = False,
        log = False,
        timeout = None,
    ):
        use_cmd = True
        cmd = ["-run=pythonscript", r"-script={}".format(python_file)]

        if fully_initialize:
            use_cmd = False
            cmd = [r'-ExecutePythonScript="{}"'.format(python_file)]

        return self.run_editor(
                argv=cmd,
                log=log,
                as_cmd=use_cmd,
                communicate=True
            )

    def run_import(self, importsettings, use_source_control = False, submit_desc="", log=False):
        try:
            cmd = ["-run=ImportAssets"]
            cmd.append(r'-importsettings="{}"'.format(importsettings))
            cmd.append("-replaceexisting")
            if not use_source_control:
                cmd.append("-nosourcecontrol")
            else:
                if submit_desc:
                    cmd.append(r'-submitdesc="{}"'.format(submit_desc))
        except:
            print("OK")
        self.run_editor(argv=cmd, as_cmd=True, communicate=True, log=log)