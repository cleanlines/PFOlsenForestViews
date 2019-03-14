from ProcessFactory import ProcessFactory
from ProcessEnum import ProcessEnum
from BaseObject import *
from Decorator import Decorator


@Decorator.timer
class UpdateViewWrapper(BaseObject):
    def run_processes(self):
        try:
            [ProcessFactory.create_process(p).run_process() for p in [ProcessEnum.SECURITY_GROUPS, ProcessEnum.CONTEXT_SERVICES, ProcessEnum.TEMPFILES]]
        except Exception as e:
            self.errorlog(str(e))

if __name__ == '__main__':
    UpdateViewWrapper().run_processes()


