from tastypie.api import Api

from DRMS.api.resources import DRMSDataSeriesResource
from DRMS.api.resources import AiaLev1FitsHeaderResource
from DRMS.api.resources import HmiIc45sFitsHeaderResource
from DRMS.api.resources import HmiM45sFitsHeaderResource

v1_api = Api(api_name='v1')
v1_api.register(DRMSDataSeriesResource())
v1_api.register(AiaLev1FitsHeaderResource())
v1_api.register(HmiIc45sFitsHeaderResource())
v1_api.register(HmiM45sFitsHeaderResource())
