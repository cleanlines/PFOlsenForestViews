import datetime
import tempfile
import os


class TempFileName(object):

    @staticmethod
    def generate_temporary_file_name(suffix, file_only=False, split=False):
        f = tempfile.NamedTemporaryFile(
            prefix=f'_ags_{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}', suffix=suffix)
        file_name = f.name
        f.close()
        if file_only:
            return os.path.split(file_name)[1]
        if split:
            return os.path.split(file_name)
        else:
            return file_name

    @staticmethod
    def get_temp_directory():
        return tempfile.tempdir
