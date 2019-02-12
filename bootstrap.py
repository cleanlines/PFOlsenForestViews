from ProcessFactory import ProcessFactory
from ProcessEnum import ProcessEnum
from BaseObject import *


class UpdateViewWrapper(BaseObject):
    def run_processes(self):
        try:
            #ProcessFactory.create_process(ProcessEnum.CORE_SERVICE).run_process()
            ProcessFactory.create_process(ProcessEnum.SECURITY_GROUPS).run_process()
            #ProcessFactory.create_process(ProcessEnum.VIEWS).run_process()
            ProcessFactory.create_process(ProcessEnum.CONTEXT_SERVICES).run_process()
            # ProcessFactory.create_process(ProcessEnum.TEMPFILES).run_process()
            # [ProcessFactory.create_process(p).run_process() for p in [ProcessEnum.CORE_SERVICE, ProcessEnum.SECURITY_GROUPS, ProcessEnum.VIEWS, ProcessEnum.CONTEXT_SERVICES, ProcessEnum.TEMPFILES]]
        except Exception as e:
            self.errorlog(str(e))


if __name__ =='__main__':
    UpdateViewWrapper().run_processes()




#ISSUE: Contours are not part of the script.
