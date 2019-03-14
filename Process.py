from __future__ import generators
from TempFileName import TempFileName
from BaseObject import *
import arcpy
from ArcGISHelper import ArcGISHelper
from Singleton import Singleton
import datetime
from CreateSDFiles import CreateSDFiles
from FileGeodatabaseHelper import FileGeodatabaseHelper
from FileHelper import FileHelper
from Decorator import Decorator


class ProcessBucket(object, metaclass=Singleton): pass


class SecurityGroupHelper(BaseObject, Process):
    @Decorator.timer
    def run_process(self):
        self.log("running SecurityGroupHelper process")
        cache = self.__process_security_groups()
        bucket = ProcessBucket()
        bucket.group_cache = cache

    @Decorator.timer
    def __process_security_groups(self):
        self.log(f"SDE connection file: {self._config.sdeconnectionfile}")
        self.log(f"Security table: {str(self._config.securitytable)}")
        current_security_groups_db = []
        current_security_groups_cache = {}

        with ArcGISHelper() as portal_helper:
            with arcpy.da.SearchCursor(f"{self._config.sdeconnectionfile}/{self._config.securitytable}", self._config.securityfields) as cursor:
                for row in cursor:
                    self.log(f"Processing: {str(row[0])}")
                    create_dict = {"title": row[0],
                                   "tags": self._config.securitytags,
                                   "access": "private", "is_invitation_only": True, "is_view_only": True}
                    if row[0]:
                        group_item = portal_helper.group_exists(row[0], self._config.securitytags, True, create_dict)
                        current_security_groups_db.append(row[0])
                        current_security_groups_cache[row[0]] = (group_item.id, row[1])
                    else:
                        self.log("No customer name for polygon skipping.")
            current_security_groups_portal = portal_helper.get_groups_from_tags(self._config.securitytags)
            #finally delete any groups that are NOT being used - content will not be shared afterwards
            groups_to_delete = [item.id for item in current_security_groups_portal if item.title not in current_security_groups_db]
            self.log(f"Groups to delete - not in security table - {str(groups_to_delete)}")
            portal_helper.delete_groups(groups_to_delete)
            self.log("Note shared items will still exist but will no longer be shared.")
            return current_security_groups_cache

    @Decorator.timer
    def current_security_groups(self):
        current_security_groups = {self._config.securityfields[0]: []}
        with arcpy.da.SearchCursor(f"{self._config.sdeconnectionfile}/{self._config.securitytable}", self._config.securityfields) as cursor:
            for row in cursor:
                current_security_groups[self._config.securityfields[0]].append(row[0])
        return current_security_groups

    class Factory:

        @staticmethod
        def create():
            return SecurityGroupHelper()


class FeatureLayerViewHelper(BaseObject, Process):
    @Decorator.timer
    def run_process(self):
        self.log("running FeatureLayerViewHelper process")
        bucket = ProcessBucket()
        if hasattr(bucket, "group_cache"):
            self.log(f"Got bucket cache: {str(bucket.group_cache)}")
            # ok we now need to build views for each customer - check if the group has any views associated with it
            with ArcGISHelper() as portal_helper:
                for k, v in bucket.group_cache.items():
                    group_id, object_id = v
                    self.log(f"Processing {k}")
                    items = portal_helper.get_shared_items_for_group(group_id, "View Service", self._config.securityviewtags.split(','))
                    self.log(f"Found these items:{str(items)}")
                    # if the items are empty then there is no view or it hasn't been shared
                    # so create it
                    if not items:
                        # get the core and context FS and create views note we should do this first
                        base_items = portal_helper.get_base_services(self._config.basesearchtags, title=self._config.title)
                        self.log(f"Found these base items {str(base_items)}")
                        # we were using the object ID but to keep it consistent with context use the name - 1st letters.
                        an_id = "".join([s[0] for s in k.split() if s.isalnum()])

                        for a_base_item in base_items:
                            item_properties = {'title': f'{a_base_item.title}_{an_id}_View',
                                               'tags': self._config.securityviewtags,
                                               'description': self._config.securityviewdescription % (k, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")),
                                               'access': 'private',
                                               'commentsEnabled': False,
                                                'securityfield': self._config.viewdefinitionfield,
                                               'viewDefinitionQuery': f"{self._config.viewdefinitionfield} = '{k}'"}

                            try:
                                item = portal_helper.create_defined_view_for_service(a_base_item, item_properties)
                                # share - we can do it directly fropm the item but then we would be introducing portal behaviour here.
                                portal_helper.share_item_with_groups_by_groupid(item, group_id)
                            except Exception as e:
                                self.errorlog(e)
                    else:
                        self.log(f"View(s) for {k} already exist and have been shared")

    class Factory:

        @staticmethod
        def create():
            return FeatureLayerViewHelper()


class CoreServiceHelper(BaseObject, Process):
    @Decorator.timer
    def run_process(self):
        sdfiles = CreateSDFiles().create_sd_files_from_map(self._config.mapname)
        ArcGISHelper().add_items_to_portal(sdfiles, self._config.basesearchtags)

    class Factory:

        @staticmethod
        def create():
            return CoreServiceHelper()


class ContextServiceHelper(BaseObject, Process):
    @Decorator.timer
    def run_process(self):
        arcpy.env.overwriteOutput = True
        groups = SecurityGroupHelper().current_security_groups()
        bucket = ProcessBucket()
        fd = list(groups.keys())[0]
        groups_to_published_items = {}

        for a_group in groups[fd]:
            with ArcGISHelper() as portal_helper:
                published_items = {}
                self.log(f"Context processing {fd}, {a_group}")
                an_id = "".join([s[0] for s in a_group.split() if s.isalnum()])
                sd_name = f"{self._config.mapname}_{an_id}"
                self.log(f"defintion name: {sd_name}")
                item_ids = portal_helper.get_named_service_definition(sd_name, self._config.contextsearchtags)
                self.log(f"Named service definitions: {str(item_ids)}")
                self.log("Looking for the replace tag")
                if item_ids and not [i for i in item_ids if self._config.replacetag in i.tags]:
                    self.log(f"Item exists and no replace tag - skipping updating {a_group} context data")
                    continue
                self.log(f"Item doesn't exist or we found the replace tag - updating {a_group} context data")
                self.log(f"Creating new ArcGIS Pro project for {a_group}")
                proj = self.create_new_prjx(fd, a_group)
                # we have done a selection on the data and created a prjx - now create the SD and share
                sdfiles = CreateSDFiles().create_sd_files_from_map(self._config.mapname, pro_prjx=proj, service_id=an_id)
                self.log(str(sdfiles))
                published_items = portal_helper.add_context_items_to_portal(sdfiles, self._config.contextsearchtags, published_items)
                groups_to_published_items[a_group] = published_items
                # refresh tags
                for i in item_ids:
                    if self._config.replacetag in i.tags:
                        self.log(f"Old tags: {i.tags}")
                        i.tags.remove(self._config.replacetag)
                        self.log(f"New tags: {i.tags}")
                        portal_helper.update_item(i, {"tags": ",".join(i.tags)})
        for a_grp, published_items in groups_to_published_items.items():
            for some_map, some_items in published_items.items():
                with ArcGISHelper() as portal_helper:
                    published_layers = portal_helper.publish_context_items_to_portal(some_map,some_items)
                    # finally share
                    if hasattr(bucket, "group_cache"):
                        try:
                            [portal_helper.share_item_with_groups_by_groupid(pi, bucket.group_cache[a_grp][0]) for pi in published_layers]
                        except Exception as e:
                            self.errorlog(str(e))

    @Decorator.timer
    def create_new_prjx(self, a_field, a_group):
        aprx = arcpy.mp.ArcGISProject(self._config.baseprjx)
        tempprjx = TempFileName.generate_temporary_file_name(suffix=".aprx")
        temp_filegeodb = FileGeodatabaseHelper().new_file_geodatabase()
        self.log(tempprjx)
        self.log(temp_filegeodb)
        aprx.saveACopy(tempprjx)
        del aprx
        self.log(f"deleted handle on {self._config.baseprjx}")
        working_aprx = arcpy.mp.ArcGISProject(tempprjx)
        self.log(f"Got {working_aprx}")
        m = working_aprx.listMaps(self._config.mapname)[0]
        lyr_file = arcpy.mp.LayerFile(self._config.layerfile)
        self.log(f"Got {lyr_file}")
        select_lyr = lyr_file.listLayers("*")[0]
        temp_lyr = "temp_lyr"
        self.log(f"making a temp feature layer with {a_field} = '{a_group}'")
        arcpy.MakeFeatureLayer_management(select_lyr, temp_lyr, f"{a_field} = '{a_group}'")
        # with arcpy.da.SearchCursor(temp_lyr, ['*']) as cursor:
        #     for row in cursor:
        #         print(row)

        # we know need to do a spatial join between the security polygon and all the other layers
        # we have to reverse the order of layers processed for the addDataFromPath
        layer_list = [l.name for l in m.listLayers("*")]
        for layer_name in reversed(layer_list):
            a_layer = m.listLayers(layer_name)[0]
            self.log(f"Processing {a_layer.name}")
            if a_layer.isBasemapLayer or not a_layer.isFeatureLayer:
                continue

            result = arcpy.GetCount_management(a_layer)
            self.log(f"before selection {a_layer.name} count:{result}")
            arcpy.SelectLayerByLocation_management(a_layer, 'INTERSECT', temp_lyr, 30)
            result = arcpy.GetCount_management(a_layer)
            self.log(f"after selection {a_layer.name} count:{result}")
            name = a_layer.dataSource.split('\\')[-1].split('.')[-1]
            self.log(f"New layer name:{name}")
            arcpy.FeatureClassToFeatureClass_conversion(a_layer, temp_filegeodb, name)
            new_layer = m.addDataFromPath(f"{temp_filegeodb}\\{name}")
            temp_lyrx_file = TempFileName().generate_temporary_file_name(suffix=".lyrx")
            self.log(f"Temp lyrx file: {temp_lyrx_file}")
            a_layer.saveACopy(temp_lyrx_file)
            arcpy.ApplySymbologyFromLayer_management(new_layer, temp_lyrx_file)
            # reset all the usual stuff
            new_layer.visible = a_layer.visible
            new_layer.maxThreshold = a_layer.maxThreshold
            new_layer.minThreshold = a_layer.minThreshold
            new_layer.showLabels = a_layer.showLabels
            new_layer.transparency = a_layer.transparency
            m.removeLayer(a_layer)
            working_aprx.save()
        fp = working_aprx.filePath
        del working_aprx
        return fp

    class Factory:

        @staticmethod
        def create():
            return ContextServiceHelper()


class CleanUpHelper(BaseObject, Process):
    @Decorator.timer
    def run_process(self):
        if self._config.cleanup:
            try:
                if self._config.cleanuplogs:
                    FileHelper().remove_all_temp_files(prefix="_ags")
                else:
                    FileHelper().remove_all_temp_files(prefix="_ags", exclude=".log")
                FileHelper().remove_all_temp_files(file_ext="sde")
            except Exception as e:
                self.errorlog(str(e))

    class Factory:

        @staticmethod
        def create():
            return CleanUpHelper()
