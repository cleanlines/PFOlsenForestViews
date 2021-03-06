from BaseObject import BaseObject
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
from Decorator import Decorator
from FileHelper import FileHelper
import datetime
import time


class ArcGISHelper(BaseObject):

    def __init__(self):
        super(ArcGISHelper, self).__init__()
        self._gis = GIS(self._config.portal, self._config.user, self._config.password, verify_cert=False)
        # override for this DEBUG session
        # DEBUG: override print
        # self.log = lambda x: print(x)
        # self.log("ArcGISHelper initialised")

    @Decorator.timer
    def get_base_services(self, tags, title):
        # NOTE: tags are important here otherwise you may get items back that you don't expect.
        item_id_list = self._gis.content.search(query=f'title:"{title}" AND tags:"{tags}"', item_type="Feature Service")
        self.log(f'title:"{title}" AND tags:"{tags}"')
        self.log(f"Found base service items: {str(item_id_list)}")
        return item_id_list

    def get_items_by_tags(self, tags,item_type):
        item_id_list = self._gis.content.search(query=f'tags:"{tags}"', item_type=item_type)
        self.log(f'tags:"{tags}"')
        self.log(f"Found items: {str(item_id_list)}")
        return item_id_list

    def get_named_service_definition(self, name, tags):
        item_id_list = self._gis.content.search(query=f'title:"{name}" AND tags:"{tags}"',
                                                item_type="Service Definition")
        self.log(f'title:"{name}" AND tags:"{tags}"')
        self.log(f"Found named services definitions: {str(item_id_list)}")
        return item_id_list

    @Decorator.timer
    def add_items_to_portal(self, sd_files, tags):
        published_items = []
        for a_map, sd in sd_files.items():
            props = self._config.itemproperties
            self.log(str(props))
            props["title"] = props["title"] % a_map
            props["description"] = self._config.sdfiledescription % (a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))
            self.log(f"Title: {props['title']}")
            a_title = props['title']
            # so we can't just add another one - it just adds another sd
            self.log(f'Looking for: title:"{a_title}" AND tags:"{tags}"')
            item_id_list = self._gis.content.search(query=f'title:"{a_title}" AND tags:"{tags}"', item_type="Service Definition")
            self.log("Found following items:")
            self.log(str(item_id_list))
            if not item_id_list:
                self.log(f"Item not found - adding")
                item = self._gis.content.add(props, sd)
                self.log(f"Added this item: {item}")
            else:
                self.log(f"Found some items - selecting this one: {item_id_list[0]}")
                item = item_id_list[0]
                self.log(f"Item {item} found - updating")
                success = item.update(item_properties={"description": self._config.sdfiledescription % (a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))}, data=sd)
                self.log(f"Item {item} found - sd updated - {success}")
            published_item = None
            try:
                self.log(f"Publishing: {str(item)}")
                published_item = item.publish(overwrite=True)
                published_item.update(item_properties={"description": self._config.featurelayerdescription % (a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))})
                self.log("Feature service updated")
                self.log(published_item)
            except Exception as big_e:
                self.errorlog(big_e)
                published_item = self.publish_remediation(item, a_map, published_item)
            except RuntimeError as e:
                #the publish may throw an error on overwrite
                self.errorlog(e)
                self.log("This is an expected error. ;-P")
                published_item = item.publish()
                published_item.update(item_properties={"description": self._config.featurelayerdescription % (a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))})
                self.log("Feature service created")
                self.log(published_item)
            published_items.append(published_item)
        return published_items

    @Decorator.timer
    def group_exists(self, group_name, tags, create=False, create_dict=None):
        # have a think about this, we pass title and tags twice
        item = self._gis.groups.search(query=f'title:"{group_name}" AND tags:"{tags}"')
        self.log(item)
        if not item and create:
            if not create_dict:
                # this may throw an error if the group exists but isn't tagged correctly.
                self.log(f"item does not exist: {item}")
                create_dict = {"title": group_name, "tags": tags}
            item = self._gis.groups.create_from_dict(dict=create_dict)
        else:
            self.log(f"item exists: {item}")

        return item[0] if isinstance(item, (list,)) else item

    @Decorator.timer
    def get_groups_from_tags(self, tags):
        return self._gis.groups.search(query=f'tags:"{tags}"')

    @Decorator.timer
    def delete_groups(self, group_ids):
        for an_id in group_ids:
            try:
                self._gis.groups.get(an_id).delete()
            except Exception as e:
                self.errorlog(e)

    @Decorator.timer
    def get_shared_items_for_group(self, group_id, type_keyword=None, tags=None):
        group = self._gis.groups.get(group_id)
        if group:
            views = group.content()
            existing_views = []
            if type_keyword:
                existing_views = [item for item in views if type_keyword in item.typeKeywords]
            if tags:
                #check tags on existing views
                existing_views = [view for view in existing_views if set(tags).issubset(view.tags)]

            return existing_views

    @Decorator.timer
    def create_defined_view_for_service(self, item, item_properties):
        flc = FeatureLayerCollection.fromitem(item)
        try:
            view_item = flc.manager.create_view(name=item_properties['title'], allow_schema_changes=False)
            view_item.update(item_properties={
                'description': item_properties['description'],
                'tags': item_properties['tags'],
                'commentsEnabled': item_properties['commentsEnabled'],
                'access': item_properties['access']
            })

            for a_layer in view_item.layers:
                if [fd for fd in a_layer.manager.properties.fields if fd.name.upper() == item_properties['securityfield'].upper()]:
                    self.log(item_properties['viewDefinitionQuery'])
                    a_layer.manager.update_definition({"viewDefinitionQuery": item_properties['viewDefinitionQuery']})
                else:
                    # filter out all the data and log
                    self.log(f"{a_layer.url} layer in the view doesn't not have {item_properties['securityfield']} field - filtering ALL data!")
                    a_layer.manager.update_definition({"viewDefinitionQuery": "OBJECTID < 1"})
                    #raise Exception(f"layer in the view doesn't not have {item_properties['securityfield']} field - aborting!")
            return view_item
        except Exception as e:
            # the view exists but hasn't been shared with this group - so we shouldn't just delete it or re share it - log it!
            self.errorlog(e)

    @Decorator.timer
    def update_item(self, an_item, props_dict):
        return an_item.update(item_properties=props_dict)

    @Decorator.timer
    def share_item_with_groups_by_groupid(self, item, group_ids):
        group_ids_not_shared = item.share(everyone=False, org=False, groups=group_ids)
        if 'notSharedWith' in group_ids_not_shared:
            return set(group_ids).issubset(group_ids_not_shared['notSharedWith'])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @Decorator.timer
    def add_context_items_to_portal(self, sd_files, tags, published_items):

        for a_map, sd in sd_files.items():
            published_items[a_map] = []
            props = self._config.itemproperties
            self.log(str(props))
            props["title"] = props["title"] % a_map
            props["description"] = self._config.sdfiledescription % (
            a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))
            self.log(f"Title: {props['title']}")
            a_title = props['title']
            # so we can't just add another one - it just adds another sd
            self.log(f'Looking for: title:"{a_title}" AND tags:"{tags}"')
            item_id_list = self._gis.content.search(query=f'title:"{a_title}" AND tags:"{tags}"',
                                                    item_type="Service Definition")
            self.log("Found following items:")
            self.log(str(item_id_list))
            if not item_id_list:
                self.log(f"Item not found - adding")  # this path works ok
                item = self._gis.content.add(props, sd)
                self.log(f"Added this item: {item}")
            else:
                self.log(f"Found some items - selecting this one: {item_id_list[0]}")
                item = item_id_list[0]
                self.log(f"Item {item} found - updating")
                success = item.update(item_properties={"description": self._config.sdfiledescription % (
                a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))}, data=sd)
                self.log(f"Item {item} found - sd updated - {success}")
            published_items[a_map].append(item)
        return published_items

    @Decorator.timer
    def publish_context_items_to_portal(self, a_map, some_items):
        published_items = []
        for item in some_items:
            published_item = None
            try:
                self.log(f"Publishing: {str(item)}")
                published_item = item.publish(overwrite=True)
                published_item.update(item_properties={"description": self._config.featurelayerdescription % (
                a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))})
                self.log("Feature service updated")
                self.log(published_item)
            except Exception as big_e:
                self.errorlog(big_e)
                published_item = self.publish_remediation(item, a_map, published_item)
            except RuntimeError as e:
                # the publish may throw an error on overwrite
                self.errorlog(e)
                self.log("This is an expected error. ;-P")
                published_item = item.publish()
                published_item.update(item_properties={"description": self._config.featurelayerdescription % (
                a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))})
                self.log("Feature service created")
                self.log(published_item)
            published_items.append(published_item)
        return published_items

    def remove_core_views(self):
        # we have to remove dependant views first
        # now we will have to recreate all the views
        tags = self._config.securityviewtags
        self.log("Views will now be broken. We have to delete and replace")
        views = self.get_items_by_tags(tags, "Feature Service")
        if views:
            self.log("Deleting views")
            for v in views:
                self.log(f"Deleting {v.name}.")
                v.delete()
                self.log(f"Deleted.")

    def publish_remediation(self, item, a_map, published_item):
        count = 0
        nap = 30
        if 'core' in item.tags:
            self.remove_core_views()

        while count != 50:
            try:
                count += 1
                published_item = item.publish(overwrite=True)
                published_item.update(item_properties={"description": self._config.featurelayerdescription % (
                    a_map, datetime.datetime.now().strftime("%d %B %Y %H:%M:%S"))})
                self.log("Have successfully republished - Breaking out of remediation loop.")
                break
            except Exception as inner_e:
                self.log(f"Republish failed on attempt: {count} - will attempt to delete the bad publish and try again")
                new_bad_item = self.get_base_services(",".join(item.tags).replace('replace', ''), item.title)
                if new_bad_item:
                    self.log("Bad feature service found - deleting (trying).")
                    new_bad_item[0].delete()
                    self.log("Bad feature service removed.")
                if count % 5 == 0:
                    nap += 15
                self.log(f"Napping for {nap} seconds and we will try again.")
                time.sleep(nap)
        return published_item
