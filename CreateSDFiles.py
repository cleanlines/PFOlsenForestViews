from BaseObject import BaseObject
from TempFileName import TempFileName
import arcpy
from Decorator import Decorator
import datetime


class CreateSDFiles(BaseObject):

    def __init__(self):
        super(CreateSDFiles, self).__init__()
        self.log("CreateSDFiles initialised")

    @Decorator.timer
    def create_sd_files_from_map(self, map_name=None, pro_prjx=None):
        sds = {}
        try:
            the_prj = pro_prjx if pro_prjx else self._config.baseprjx
            aprx = arcpy.mp.ArcGISProject(the_prj)
            if map_name in [m.name for m in aprx.listMaps()]:
                service_object = getattr(self._config, map_name.lower())
                service_name = service_object["servicename"]
                sddraft_file = TempFileName.generate_temporary_file_name(suffix=".sddraft")
                sdfile = TempFileName.generate_temporary_file_name(suffix=".sd")
                m = aprx.listMaps(map_name)[0]
                arcpy.SignInToPortal(self._config.portal, self._config.user, self._config.password)
                sharing_draft = m.getWebLayerSharingDraft("HOSTING_SERVER", "FEATURE", service_name)
                sharing_draft.summary = service_object["summary"]
                sharing_draft.tags = service_object["tags"]
                sharing_draft.description = service_object["description"] + f'<br/>Item updated on {datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")} by automated script.'
                sharing_draft.credits = ""
                sharing_draft.exportToSDDraft(sddraft_file)
                arcpy.StageService_server(sddraft_file, sdfile)
                sds[map_name] = sdfile
                #sds.append()
        except Exception as e:
            self.errorlog(e)
        return sds

# if __name__ =='__main__':
#     print(CreateSDFiles().create_sd_files_from_maps())
