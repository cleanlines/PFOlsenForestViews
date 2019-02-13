firstly upgrade the python environment to the latest version of arcgis api - you may need to create a new env on the server then upgrade
https://developers.arcgis.com/python/guide/install-and-set-up/#Upgrade-the-arcgis-package

conda upgrade -c esri arcgis

The script works by performing the following workflow:
From a pre configured ArcGIS Pro project with two maps it does the following:
  * Creates a sd file from the Core data. This picks up any edits that may have happened.
  * Caches all the current forestry security groups and creates groups in the portal for any new groups.
  * Creates hosted feature layer views for each security polygon
  * Creates a data extract for each contextual dataset by group polygon except for contours.

need to set arcgis pro licence to offline and may need to run via propy.bat

http://pro.arcgis.com/en/pro-app/arcpy/get-started/using-conda-with-arcgis-pro.htm

https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python