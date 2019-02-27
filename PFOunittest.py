print("helloworld")
import sys
print(sys.path)
print("Testing imports")
from ProcessFactory import ProcessFactory
from ProcessEnum import ProcessEnum
from BaseObject import *
from Decorator import Decorator
print("imports ok")

@Decorator.timer
class UpdateViewWrapper(BaseObject):
    def run_processes(self):
        try:
            ProcessFactory.create_process(ProcessEnum.SECURITY_GROUPS).run_process()
        except Exception as e:
            self.errorlog(str(e))


if __name__ == '__main__':
    UpdateViewWrapper().run_processes()
