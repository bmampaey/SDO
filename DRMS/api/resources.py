from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from DRMS.models import DRMSDataSeries
from DRMS.models import AiaLev1FitsKeyword, AiaLev1FitsHeader
from DRMS.models import HmiIc45sFitsKeyword, HmiIc45sFitsHeader
from DRMS.models import HmiM45sFitsKeyword, HmiM45sFitsHeader

class DRMSDataSeriesResource(ModelResource):
	class Meta:
		queryset = DRMSDataSeries.objects.all()
		resource_name = 'data_series'
		filtering = {
			'name': ALL,
		}

class AiaLev1FitsKeywordResource(ModelResource):
	class Meta:
		queryset = AiaLev1FitsKeyword.objects.all()
		resource_name = 'aia_lev1_fits_keyword'
		filtering = {
			'keyword': ALL,
			'unit': ALL,
			'comment': ALL,
		}

class AiaLev1FitsHeaderResource(ModelResource):
	class Meta:
		queryset = AiaLev1FitsHeader.objects.all()
		resource_name = 'aia_lev1_fits_header'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'date_obs': ALL,
			'wavelnth': ALL,
			'quality': ALL
		}

class HmiIc45sFitsKeywordResource(ModelResource):
	class Meta:
		queryset = HmiIc45sFitsKeyword.objects.all()
		resource_name = 'hmi_ic_45s_fits_keyword'
		filtering = {
			'keyword': ALL,
			'unit': ALL,
			'comment': ALL,
		}

class HmiIc45sFitsHeaderResource(ModelResource):
	class Meta:
		queryset = HmiIc45sFitsHeader.objects.all()
		resource_name = 'hmi_ic_45s_fits_header'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'date_obs': ALL,
			'wavelnth': ALL,
			'quality': ALL
		}

class HmiM45sFitsKeywordResource(ModelResource):
	class Meta:
		queryset = HmiM45sFitsKeyword.objects.all()
		resource_name = 'hmi_m_45s_fits_keyword'
		filtering = {
			'keyword': ALL,
			'unit': ALL,
			'comment': ALL,
		}

class HmiM45sFitsHeaderResource(ModelResource):
	class Meta:
		queryset = HmiM45sFitsHeader.objects.all()
		resource_name = 'hmi_m_45s_fits_header'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'date_obs': ALL,
			'wavelnth': ALL,
			'quality': ALL
		}
