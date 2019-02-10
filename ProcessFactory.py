from __future__ import generators
from Process import *


class ProcessFactory(object):
    factories = {}

    @staticmethod
    def add_factory(process_id, process_factory):
        ProcessFactory.factories.put[process_id] = process_factory

    @staticmethod
    def create_process(process_id):
        print(f"process id:{process_id}")
        types = [t.__name__ for t in Process.__subclasses__()]
        if process_id.value not in types:
            raise Exception(f"{process_id} is not a valid Process")
        if process_id not in ProcessFactory.factories:
            ProcessFactory.factories[process_id] = \
                eval(f"{process_id.value}.Factory()")
        return ProcessFactory.factories[process_id].create()


