from enum import Enum
from enum import auto
from enum import unique

@unique
class ProcessEnum(Enum):
    CORE_SERVICE = 'CoreServiceHelper'
    CONTEXT_SERVICES = 'ContextServiceHelper'
    SECURITY_GROUPS = 'SecurityGroupHelper'
    SHARING = 'SharingHelper'
    VIEWS = 'FeatureLayerViewHelper'
    TEMPFILES = 'CleanUpHelper'

