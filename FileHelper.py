from BaseObject import BaseObject
from TempFileName import TempFileName
import fnmatch
import os


class FileHelper(BaseObject):

    def __init__(self):
        super(FileHelper, self).__init__()
        self.log("FileHelper initialised")

    def remove_all_temp_files(self, file_ext="*", prefix=""):
        for root, dirnames, filenames in os.walk(TempFileName.get_temp_directory()):
            for filename in fnmatch.filter(filenames, f'{prefix}*.{file_ext}'):
                try:
                    os.remove(os.path.join(root,filename))
                except WindowsError as we:
                    self.log("Failed to delete: %s" % filename)
                    self.log(we.strerror)
                except Exception as e:
                    self.log("Failed to delete: %s" % filename)
                    self.errorlog(e.message)

    def delete_file(self, filename):
        try:
            os.remove(filename)
        except WindowsError as we:
            self.log("Failed to delete: %s" % filename)
            self.log(we.strerror)
        except Exception as e:
            self.log("Failed to delete: %s" % filename)
            self.errorlog(e.message)


# if __name__ == "__main__":
#     fh = FileHelper()
#     fh.remove_all_temp_files("csv")