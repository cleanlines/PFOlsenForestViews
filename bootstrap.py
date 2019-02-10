from ArcGISHelper import ArcGISHelper
from ProcessFactory import ProcessFactory
from ProcessEnum import ProcessEnum

'''
we need a different process for the context stuff
check for existence of the HFL for context data and republish if not there
do a spatial join with the security polygon then apply a definition query.
then publish as a HFL from the sd to the group

'''

if __name__ =='__main__':

    #ProcessFactory.create_process(ProcessEnum.CONTEXT_SERVICES).run_process()
    #ProcessFactory.create_process(p).run_process()  ProcessEnum.CORE_SERVICE,
    [ProcessFactory.create_process(p).run_process() for p in [ProcessEnum.SECURITY_GROUPS, ProcessEnum.VIEWS, ProcessEnum.CONTEXT_SERVICES]]

#TODO: if SD doesn't exist but HFL does it tries to publish the SD - BOOM!

#TODO: if group exists but isn't found BOOM as it tries to create it - is it the tags?