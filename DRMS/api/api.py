from tastypie.api import Api

from DRMS.api.resources import DRMSDataSeriesResource
from DRMS.api.resources import  AiaLev1Resource, AiaLev1FitsKeywordResource, AiaLev1FitsHeaderResource

v1_api = Api(api_name='v1')
v1_api.register(DRMSDataSeriesResource())
v1_api.register(AiaLev1FitsKeywordResource())
v1_api.register(AiaLev1FitsHeaderResource())
v1_api.register(HmiFitsKeywordResource())
v1_api.register(AiaLev1FitsHeaderResource())
v1_api.register(AiaLev1FitsKeywordResource())
v1_api.register(AiaLev1FitsHeaderResource())
