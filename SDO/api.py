from tastypie.api import Api

from PMD.api.resources import DataSeriesResource
from PMD.api.resources import AiaLev1Resource
from PMD.api.resources import HmiIc45SResource
from PMD.api.resources import HmiM45SResource

v1_api = Api(api_name='v1')
v1_api.register(DataSeriesResource())
v1_api.register(AiaLev1Resource())
v1_api.register(HmiIc45SResource())
v1_api.register(HmiM45SResource())
