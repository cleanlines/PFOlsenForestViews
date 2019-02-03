import arcpy
import importlib
import BaseObject
import BaseLogger
import Logger
import JSONConfig
import TempFileName
import Singleton


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "PFOlsenTools"
        self.alias = "PFOlsenTools"
        # List of tool classes associated with this toolbox
        self.tools = [CreateNewSDFile, ReloadModules, ShowTempDir]


class CommonTool(object):
    def __init__(self):
        self.aplog = lambda msg : arcpy.AddMessage(str(msg))
        self.aperror_log = lambda msg : arcpy.AddError(str(msg))
        arcpy.SetLogHistory(False)

#TODO: Review this for how we create Context Data (e.g. the service naming - make it the same as the bootstrap)

class CreateNewSDFile(BaseObject.BaseObject, CommonTool):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        CommonTool.__init__(self)
        BaseObject.BaseObject.__init__(self)
        self.label = "CreateNewSDFile"
        self.description = "Creates a new SD file for any changes made in a map project to the core and context services"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None

        param0 = arcpy.Parameter(
            displayName="Input Map",
            name="in_map",
            datatype="GPMap",
            parameterType="Required",
            direction="Input")

        # needs to reflect the values in common config
        param1 = arcpy.Parameter(
            displayName="PF Olsen Service Definition",
            name="sd_layer",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        self.log(self._config)

        param1.filter.list = self._config.sdfilelist
        return [param0, param1]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        map_name = parameters[0].value
        self.aplog(f"Regenerating sd files based on current map {map_name}")
        outfile = f"{self._config.sdfileoutlocation}/{parameters[1].value}"

        service_object = getattr(self._config, parameters[1].value)
        service_name = service_object["servicename"]
        sddraft_file = TempFileName.TempFileName.generate_temporary_file_name(suffix=".sddraft")
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        m = aprx.listMaps(map_name)[0]
        arcpy.SignInToPortal(self._config.portal, self._config.user, self._config.password)
        sharing_draft = m.getWebLayerSharingDraft("HOSTING_SERVER", "FEATURE", service_name)
        sharing_draft.summary = service_object["summary"]
        sharing_draft.tags = service_object["tags"]
        sharing_draft.description = service_object["description"]
        sharing_draft.credits = ""
        self.aplog(sddraft_file)
        self.aplog("Creating the sddraft this may take a moment")
        sharing_draft.exportToSDDraft(sddraft_file)
        arcpy.StageService_server(sddraft_file, outfile)
        self.aplog(f"Created {outfile} for {map_name}")
        return


class ShowTempDir(CommonTool):
    def __init__(self):
        super().__init__()
        """Define the tool (tool name is the name of the class)."""
        self.label = "Show temp Dir"
        self.description = "Show temp Dir"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        self.aplog("Temp Dir")
        self.aplog(str(TempFileName.TempFileName.get_temp_directory()))



class ReloadModules(CommonTool):
    def __init__(self):
        super().__init__()
        """Define the tool (tool name is the name of the class)."""
        self.label = "Reload Modules"
        self.description = "Reload Modules"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        self.aplog("Reloading modules")
        modules = [BaseObject, BaseLogger, Logger, JSONConfig, TempFileName, Singleton]
        for x in modules:
            self.aplog("reloading {0}".format(str(x)))
            importlib.reload(x)
#
# if __name__ =='__main__':
#     tbx = Toolbox()
#     tool = CreateNewSDFile()
#     tool.execute(tool.getParameterInfo(),None)
