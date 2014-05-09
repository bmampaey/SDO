from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from DRMS.models import DRMSDataSeries
from DRMS.models import AiaLev1, AiaLev1FitsKeyword, AiaLev1FitsHeader

def utc_to_offset(utc):
	

class DRMSDataSeriesResource(ModelResource):
	class Meta:
		queryset = DRMSDataSeries.objects.all()
		resource_name = 'data_series'
		filtering = {
			'name': ALL,
		}

class AiaLev1Resource(ModelResource):
	class Meta:
		queryset = AiaLev1.objects.all()
		resource_name = 'aia_lev1'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'date_obs': ALL,
			'wavelnth': ALL,
			'quality': ALL
		}
		
		def dehydrate_date_obs(self, bundle):
			return offset_to_utc(bundle.data['date_obs'])
		
		def hydrate_date_obs(self, bundle):
			bundle.data['date_obs'] = int(utc_to_offset(bundle.data['date_obs']))
			return bundle

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
