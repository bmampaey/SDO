from tastypie.api import Api

# Create the api
v1_api = Api(api_name='v1')

# Add DRMS resources
from DRMS.resources import DRMSDataSeriesResource
from DRMS.resources import AiaLev1FitsHeaderResource
from DRMS.resources import HmiIc45sFitsHeaderResource
from DRMS.resources import HmiM45sFitsHeaderResource

v1_api.register(DRMSDataSeriesResource())
v1_api.register(AiaLev1FitsHeaderResource())
v1_api.register(HmiIc45sFitsHeaderResource())
v1_api.register(HmiM45sFitsHeaderResource())

# Add PMD ressources
from PMD.resources import DataSeriesResource
from PMD.resources import AiaLev1Resource
from PMD.resources import HmiIc45SResource
from PMD.resources import HmiM45SResource

v1_api.register(DataSeriesResource())
v1_api.register(AiaLev1Resource())
v1_api.register(HmiIc45SResource())
v1_api.register(HmiM45SResource())


