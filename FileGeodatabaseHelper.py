from TempFileName import TempFileName
from BaseObject import BaseObject
import arcpy
import shelve

class FileGeodatabaseHelper(BaseObject):

    def __init__(self):
        super(FileGeodatabaseHelper,self).__init__()
        # self._clean_up = False
        self._current_file_geodb = None
        self.log("FileGeodatabaseHelper initialised")

    @property
    def current_file_geodb(self):
        return self._current_file_geodb

    @current_file_geodb.setter
    def current_file_geodb(self, value):
        if arcpy.Exists(value):
            self._current_file_geodb = value
        else:
            self._current_file_geodb = None

    def new_file_geodatabase(self):
        self._delete_current_file_geodb()
        path, file_geodb_name = TempFileName.generate_temporary_file_name(".gdb", split=True)
        self._current_file_geodb = arcpy.CreateFileGDB_management(path,file_geodb_name)[0]
        self.log("File geodb created at: %s" % self._current_file_geodb)
        return self._current_file_geodb

    def new_file_geodatabase_with_name(self, name):
        loc = "%s/%s.gdb" % (TempFileName.get_temp_directory(), name)
        if arcpy.Exists(loc):
            try:
                self.log("Cleaning up file geodb %s" % loc)
                arcpy.Delete_management(loc)
            except Exception as e:
                self.errorlog(e.message)
        try:
            self._current_file_geodb = arcpy.CreateFileGDB_management(TempFileName.get_temp_directory(), name)[0]
            self.log("File geodb created at: %s" % self._current_file_geodb)
            return self._current_file_geodb
        except Exception as e:
            self.errorlog(e.message)
            return self._current_file_geodb

    def cache_database_name(self):
        s = shelve.open("%s%s%s" % (TempFileName.get_temp_directory(), "/", self._config.shelf))
        s['fwpgeodb'] = self._current_file_geodb
        s.close()

    def _delete_current_file_geodb(self):
        if self._current_file_geodb and self._clean_up:
            try:
                self.log("Cleaning up file geodb %s" % str(self._current_file_geodb))
                arcpy.Delete_management(self._current_file_geodb)
            except Exception as e:
                self.errorlog(e.message)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # clean up the file geodb
        self._delete_current_file_geodb()