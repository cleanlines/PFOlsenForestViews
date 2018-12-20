
from BaseObject import BaseObject
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.features import FeatureLayerCollection
from Decorator import Decorator
from CreateSDFiles import CreateSDFiles
import datetime


class ArcGISHelper(BaseObject):

    def __init__(self):
        super(ArcGISHelper, self).__init__()
        self._gis = GIS(self._config.portal, self._config.user, self._config.password)
        # override for this DEBUG session
        # TODO: remove debug print
        self.log = lambda x: print(x)
        self.log("ArcGISHelper initialised")

    def get_base_services(self): #
        item_id_list = self._gis.content.search(query=f'title:"_Data" AND tags:"{self._config.basesearchtags}"', item_type="Feature Service")
        print(item_id_list)
        return item_id_list

    @Decorator.timer
    def add_items_to_portal(self, sd_files):
        #sd_files = CreateSDFiles().create_sd_files_from_maps()
        for a_map, sd in sd_files.items():
            props = self._config.itemproperties
            props["title"] = props["title"] % a_map
            # so we can't just add another one - it just adds another sd

            item_id_list = self._gis.content.search(query=f'title:"{a_map}_Data" AND tags:"{self._config.basesearchtags}"',item_type="Service Definition")
            if not item_id_list:
                self.log(f"Item not found - adding")
                item = self._gis.content.add(props, sd)
                print(item)
            else:
                print(item_id_list[0])
                item = item_id_list[0]
                self.log(f"Item {item} found - updating")
                item.update(item_properties={"description":self._config.sdfiledescription % (a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))}, data=sd)
                self.log(f"Item {item} found - sd updated")
            published_item = None
            try:

                published_item = item.publish(overwrite=True) # issue - overwrite # check existence
                published_item.update(item_properties={"description": self._config.featurelayerdescription % (a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))})
                self.log("Feature service updated")
                self.log(published_item)
            except RuntimeError as e:
                self.errorlog(e)
                published_item = item.publish()  # issue - overwrite # check existence
                published_item.update(item_properties={"description": self._config.featurelayerdescription % (a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))})
                self.log("Feature service created")
                self.log(published_item)

    def group_exists(self, group_name, tags, create=False, create_dict=None):
        # have a think about this, we pass title and tags twice
        item = self._gis.groups.search(query=f'title:"{group_name}" AND tags:"{tags}"')
        self.log(item)
        if not item and create:
            if not create_dict:
                create_dict = {"title": group_name, "tags": tags}
            item = self._gis.groups.create_from_dict(dict=create_dict)
        else:
            self.log(f"item exists: {item}")
        return item[0] if len(item) else item

    def get_groups_from_tags(self, tags):
        return self._gis.groups.search(query=f'tags:"{tags}"')

    def delete_groups(self, group_ids):
        for id in group_ids:
            try:
                self._gis.groups.get(id).delete()
            except Exception as e:
                self.errorlog(e)

    def get_shared_items_for_group(self, group_id, type_keyword=None, tags=None):

        group = self._gis.groups.get(group_id)
        if group:
            views = group.content()
            if type_keyword:
                views = [item for item in views if type_keyword in item.typeKeywords]
            if tags:
                views = [view for view in views if set(tags).issubset(view.tags)]

            return views

    def create_defined_view_for_service(self, item, item_properties):
        flc = FeatureLayerCollection.fromitem(item)
        try:
            view_item = flc.manager.create_view(name=item_properties['title'], allow_schema_changes=False)
            print(view_item)
            # https://febsvr.australiaeast.cloudapp.azure.com/server/rest/admin/services/Hosted/Core_Data_View/FeatureServer/0/updateDefinition
            #{"viewDefinitionQuery":"bp_name = 'OTPP New Zealand Forest Investments Limited'"}

            # data = view_item.get_data()
            view_item.update(item_properties={
                'description': item_properties['description'],
                'tags': item_properties['tags'],
                'commentsEnabled': item_properties['commentsEnabled'],
                'access': item_properties['access']
            })

            for a_layer in view_item.layers:
                if [fd for fd  in a_layer.manager.properties.fields if fd.name.upper() == item_properties['securityfield'].upper()]:
                    self.log(item_properties['viewDefinitionQuery'])
                    a_layer.manager.update_definition({"viewDefinitionQuery": item_properties['viewDefinitionQuery']})
                    print('a')
                else:
                    # filter out all the data and log
                    self.log(f"{a_layer.url} layer in the view doesn't not have {item_properties['securityfield']} field - filtering ALL data!")
                    a_layer.manager.update_definition({"viewDefinitionQuery": "OBJECTID < 1"})
                    #raise Exception(f"layer in the view doesn't not have {item_properties['securityfield']} field - aborting!")
            return view_item
        except Exception as e:
            # the view exists but hasn't been shared with this group - so we shouldn't just delete it or re share it - log it!
            self.errorlog(e)

    def share_item_with_groups_by_groupid(self,item, group_ids):
        group_ids_not_shared = item.share(everyone=False,org=False,groups=group_ids)
        groups_to_share_with = group_ids.split(",")
        if 'notSharedWith' in group_ids_not_shared:
            return set(group_ids).issubset(group_ids_not_shared['notSharedWith'])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass





