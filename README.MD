firstly upgrade the python environment to the latest version of arcgis api - you may need to create a new env on the server then upgrade
https://developers.arcgis.com/python/guide/install-and-set-up/#Upgrade-the-arcgis-package

conda upgrade -c esri arcgis

The script works by publishing a sd file to the server which will over write the data each time. If you decide to change the service then redo the SD file from the supplied toolbox.

need to set arcgis pro licence to offline and may need to run via propy.bat

http://pro.arcgis.com/en/pro-app/arcpy/get-started/using-conda-with-arcgis-pro.htm

https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python