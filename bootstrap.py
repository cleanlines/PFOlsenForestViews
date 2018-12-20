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
    #print(ArcGISHelper().add_items_to_portal())
    #print(ProcessFactory)
    #ArcGISHelper().get_base_services()
    [ProcessFactory.create_process(p).run_process() for p in [ProcessEnum.CORE_SERVICE, ProcessEnum.CONTEXT_SERVICES,
                                                              ProcessEnum.SECURITY_GROUPS, ProcessEnum.VIEWS]]


