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

    ProcessFactory.create_process(ProcessEnum.CORE_SERVICE).run_process()
    ProcessFactory.create_process(ProcessEnum.SECURITY_GROUPS).run_process()
    ProcessFactory.create_process(ProcessEnum.VIEWS).run_process()
    #ProcessFactory.create_process(ProcessEnum.CONTEXT_SERVICES).run_process()
    #ProcessFactory.create_process(ProcessEnum.TEMPFILES).run_process()

    # [ProcessFactory.create_process(p).run_process() for p in [ProcessEnum.CORE_SERVICE, ProcessEnum.SECURITY_GROUPS, ProcessEnum.VIEWS, ProcessEnum.CONTEXT_SERVICES, ProcessEnum.TEMPFILES]]

#TODO: if SD doesn't exist but HFL does it tries to publish the SD - BOOM!

#TODO: if group exists but isn't found BOOM as it tries to create it - is it the tags?
#BUG: brings back Context Views - fixed by changing keywords

#ISSUE: Contours are not part of the script.
#ISSUE: Sometimes upload doesn't come back

#Didn't find exisiting contxt SD
#issue - can there be more than one?
#when finding multiple items only works on first one

#should we do a replace on the core data?