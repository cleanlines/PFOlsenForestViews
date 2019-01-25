from __future__ import generators

from TempFileName import TempFileName
from BaseObject import *
from Decorator import Decorator
import arcpy
from ArcGISHelper import ArcGISHelper
from Singleton import Singleton
import datetime
from CreateSDFiles import CreateSDFiles


class ProcessBucket(object, metaclass=Singleton): pass


class SecurityGroupHelper(BaseObject, Process):
    def run_process(self):
        self.log("running SecurityGroupHelper process")
        cache = self.__process_security_groups()
        bucket = ProcessBucket()
        bucket._group_cache = cache

    @Decorator.timer
    def __process_security_groups(self):
        # should really push this into a cursor access class - put a yield on it - see csvhelper
        # would be more elegant
        print(self._config.sdeconnectionfile)
        print(self._config.securitytable)
        current_security_groups_db = []
        current_security_groups_cache = {}

        with ArcGISHelper() as portal_helper:
            with arcpy.da.SearchCursor(f"{self._config.sdeconnectionfile}/{self._config.securitytable}", self._config.securityfields) as cursor:
                for row in cursor:
                    print(row[0])
                    create_dict = {"title": row[0],
                                   "tags": self._config.securitytags,
                                   "access": "private", "is_invitation_only": True, "is_view_only": True}
                    group_item = portal_helper.group_exists(row[0], self._config.securitytags, True, create_dict)
                    current_security_groups_db.append(row[0])
                    current_security_groups_cache[row[0]] = (group_item.id, row[1])
            current_security_groups_portal = portal_helper.get_groups_from_tags(self._config.securitytags)
            print(current_security_groups_portal)
            #finally delete any groups that are NOT being used - what do we do with content shared with it...?
            groups_to_delete = [item.id for item in current_security_groups_portal if item.title not in current_security_groups_db]
            print(groups_to_delete)
            portal_helper.delete_groups(groups_to_delete)
            return current_security_groups_cache

    def current_security_groups(self):
        current_security_groups = {self._config.securityfields[0]: []}
        with arcpy.da.SearchCursor(f"{self._config.sdeconnectionfile}/{self._config.securitytable}", self._config.securityfields) as cursor:
            for row in cursor:
                print(row[0])
                current_security_groups[self._config.securityfields[0]].append(row[0])
        return current_security_groups

    class Factory:

        @staticmethod
        def create():
            return SecurityGroupHelper()


class FeatureLayerViewHelper(BaseObject, Process):
    def run_process(self):
        self.log("running FeatureLayerViewHelper process")
        bucket = ProcessBucket()
        if hasattr(bucket,"_group_cache"):
            print(bucket._group_cache)
            # ok we now need to build views for each customer - check if the group has any views associated with it
            with ArcGISHelper() as portal_helper:
                for k, v in bucket._group_cache.items():
                    group_id, object_id = v
                    self.log(f"Processing {k}")
                    print(f"Processing {k}")
                    # only do one keyword at a time or we could have issues (where ite,s have same keyowrds - does it matter?)
                    items = portal_helper.get_shared_items_for_group(group_id, "View Service",self._config.securityviewtags)
                    # we need the object id (or customer id) to differentiate the views
                    # type is Feature Service
                    # typeKeywords <class 'list'>: ['ArcGIS Server', 'Data', 'Feature Access', 'Feature Service', 'providerSDS', 'Service', 'Hosted Service', 'View Service']
                    print(items)
                    # if the items are empty then there is no view or it hasn't been shared
                    # so create it
                    if not items:
                        # get the core and context FS and create views
                        base_items = portal_helper.get_base_services()
                        print(base_items)
                        for a_base_item in base_items:
                            item_properties = {'title':f'{a_base_item.title}_{object_id}_View',
                                               'tags': self._config.securityviewtags,
                                               'description': self._config.securityviewdescription %(k, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")),
                                               'access':'private',
                                               'commentsEnabled': False,
                                                'securityfield':self._config.viewdefinitionfield,
                                               'viewDefinitionQuery': f"{self._config.viewdefinitionfield} = '{k}'"}

                            try:
                                item = portal_helper.create_defined_view_for_service(a_base_item, item_properties)
                                # share - we can do it directly fropm the item but then we would be introducing portal behaviour here.
                                portal_helper.share_item_with_groups_by_groupid(item, group_id)
                            except Exception as e:
                                self.errorlog(e)
                            # DEBUG return
                    else:
                        print("View already exists and is shared")

    class Factory:

        @staticmethod
        def create():
            return FeatureLayerViewHelper()


class CoreServiceHelper(BaseObject, Process):
    def run_process(self):
        sdfiles = CreateSDFiles().create_sd_files_from_map(self._config.mapname)
        ArcGISHelper().add_items_to_portal(sdfiles)

    class Factory:

        @staticmethod
        def create():
            return CoreServiceHelper()


class ContextServiceHelper(BaseObject, Process):
    def run_process(self):
        # we need to process the project - set definitions then publish
        # so some looping etc
        #we have to create a context for each security group
        arcpy.env.overwriteOutput = True
        groups = SecurityGroupHelper().current_security_groups()
        fd = list(groups.keys())[0]
        for a_group in groups[fd]:
            print(fd, a_group)
            self.create_new_prjx(fd, a_group)


        #CreateSDFiles().create_sd_files_from_map(self._config.coremapname,pro_prjx=new_prjx)
        #ArcGISHelper().add_items_to_portal() # this function needs to be slightly modified - not generic enough

        #### NOTE!!! Removed the secured BP zone from the base project
    def create_new_prjx(self, a_field, a_group):
        aprx = arcpy.mp.ArcGISProject(self._config.baseprjx)
        tempprjx = TempFileName.generate_temporary_file_name(suffix=".aprx")
        print(tempprjx)
        aprx.saveACopy(tempprjx)
        working_aprx = arcpy.mp.ArcGISProject(tempprjx)
        m = working_aprx.listMaps(self._config.mapname)[0]
        lyr_file = arcpy.mp.LayerFile(self._config.layerfile)

        select_lyr = lyr_file.listLayers("*")[0]
        temp_lyr = "temp_lyr"
        arcpy.MakeFeatureLayer_management(select_lyr, temp_lyr, f"{a_field} = '{a_group}'")
        print("temp layer,",f"{a_field} = '{a_group}'")
        with arcpy.da.SearchCursor(temp_lyr, ['*']) as cursor:
            for row in cursor:
                print(row)

        # we know need to do a spatial join between the security polygon and all the other layers
        count = 0
        for a_layer in m.listLayers("*"):
            print(a_layer.name)
            if a_layer.isBasemapLayer:
                continue

            result = arcpy.GetCount_management(a_layer)
            print("before selection ", a_layer.name, f"count:{result}")
            arcpy.SelectLayerByLocation_management(a_layer, 'INTERSECT', temp_lyr, 30)
            count += 1
            result = arcpy.GetCount_management(a_layer)
            print("after selection ", a_layer.name, f"count:{result}")
            working_aprx.save()

        print(working_aprx.filePath)

        # dec 2018 you wrere here. you were lookig at doing the selection and then publishing - the selection happens but when you save the prjx the selections aren't there. Once you've done that you need to publish. Note you have to change the publish process as this reads local config and won't name the service the right thing - you will have to update to make sure the conext service format is the same as the core views - context_data_object_id_service or something.
        sdfiles = CreateSDFiles().create_sd_files_from_map(self._config.mapname, pro_prjx=working_aprx.filePath)
        ArcGISHelper().add_items_to_portal(sdfiles)
        #arcpy.Delete_management(temp_lyr)

    class Factory:

        @staticmethod
        def create():
            return ContextServiceHelper()
