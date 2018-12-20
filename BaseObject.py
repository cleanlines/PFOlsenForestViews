from JSONConfig import JSONConfig
from BaseLogger import BaseLogger


class Process(object): pass


class BaseObject(BaseLogger):

    def __init__(self):
        super(BaseObject, self).__init__()
        self._class_name = self.__class__.__name__
        self._config = JSONConfig(class_name=self._class_name)
        self.log(f"Class:{self._class_name}")
        #self.log("BaseObject initialised")
