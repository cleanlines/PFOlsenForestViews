import inspect
import os
import json
from BaseLogger import BaseLogger


class JSONConfig(BaseLogger):

    def __init__(self, class_name=None):
        super(JSONConfig, self).__init__()

        try:
            if class_name is not None:
                a_file = inspect.getframeinfo(inspect.currentframe())[0]
                self._common_config = os.path.join(os.path.split(a_file)[0], 'commonconfig.json')
                self._file = os.path.join(os.path.split(a_file)[0], class_name + '.json')
                self._logger.do_message(f"loaded config for {class_name} from {self._file}", "info")
                if os.path.exists(self._common_config):
                    self.__mixin_config(self._common_config)

                if os.path.exists(self._file):
                    self.__mixin_config(self._file)
                else:
                    self._logger.do_message(f"Configuration file not found - {class_name}", "info")

        except Exception:
            # no config file found - may or may not be an error depending on the module.
            raise RuntimeError("Cannot load module configuration")
        self._logger.do_message("JSONConfig initialised")

    def __mixin_config(self, a_file):
        try:
            json_data = open(a_file)
            config = json.load(json_data)
            json_data.close()
            [setattr(self, k, v) for k, v in config.items()]

        except Exception:
            self._logger.do_message("Cannot load application configuration", "err")
            raise RuntimeError("Cannot load application configuration")

    def __str__(self):
        return self._file
